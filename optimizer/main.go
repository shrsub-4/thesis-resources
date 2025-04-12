package main

import (
	"context"
	"fmt"
	"sort"
	"time"

	influxdb2 "github.com/influxdata/influxdb-client-go/v2"
	"github.com/prometheus/client_golang/api"
	v1 "github.com/prometheus/client_golang/api/prometheus/v1"
	"github.com/prometheus/common/model"
)

const (
	promURL      = "http://10.104.8.215:31070"
	influxURL    = "http://localhost:8086"
	influxToken  = "i-WSt-nQZg2gSzIGJ7DNzJvCNtF6gsRFHaqR8DUQevU-HOixpbsNaztZxa6-M5Yj_OSWks7uF83lRnVtpoqV-g=="
	influxOrg    = "your-org"
	influxBucket = "metrics"
)

const K = 30

func main() {
	go startCollectorLoop(5 * time.Second)
	go startOptimizerLoop(K * time.Second)

	select {}
}

func startCollectorLoop(interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	promClient, _ := api.NewClient(api.Config{Address: promURL})
	prom := v1.NewAPI(promClient)

	influx := influxdb2.NewClient(influxURL, influxToken)
	writeAPI := influx.WriteAPIBlocking(influxOrg, influxBucket)

	for range ticker.C {
		timestamp := time.Now()

		latency := queryPrometheus(prom, `
		(
		  histogram_quantile(0.95, sum(irate(istio_request_duration_milliseconds_bucket{
			reporter="source",
			connection_security_policy="mutual_tls",
			source_workload=~"appservice-00003-deployment",
			source_workload_namespace=~"default",
			destination_service=~"db-service\\.default\\.svc\\.cluster\\.local"
		  }[1m])) by (destination_service, le)) / 1000
		)
		or
		(
		  histogram_quantile(0.95, sum(irate(istio_request_duration_seconds_bucket{
			reporter="source",
			connection_security_policy="mutual_tls",
			source_workload=~"appservice-00003-deployment",
			source_workload_namespace=~"default",
			destination_service=~"db-service\\.default\\.svc\\.cluster\\.local"
		  }[1m])) by (destination_service, le))
		)
		`)

		traffic := queryPrometheus(prom, `
		histogram_quantile(0.95, sum(irate(istio_request_bytes_bucket{
		  reporter="source",
		  connection_security_policy!="mutual_tls",
		  source_workload=~"appservice-00003-deployment",
		  source_workload_namespace=~"default",
		  destination_service=~"db-service\\.default\\.svc\\.cluster\\.local"
		}[1m])) by (destination_service, le))
		`)
		vector := queryVector(prom, `sum(rate(container_cpu_usage_seconds_total{pod=~"appservice.*"}[1m])) by (instance)`)

		for _, sample := range vector {
			node := string(sample.Metric["instance"])
			cpu := float64(sample.Value)

			point := influxdb2.NewPoint("node_metrics",
				map[string]string{"node": node},
				map[string]interface{}{
					"cpu":     cpu,
					"latency": latency,
					"traffic": traffic,
				},
				timestamp,
			)

			_ = writeAPI.WritePoint(context.Background(), point)
		}
	}
}

func startOptimizerLoop(interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	client := influxdb2.NewClient(influxURL, influxToken)
	queryAPI := client.QueryAPI(influxOrg)

	for range ticker.C {
		query := `
		from(bucket: "metrics")
		|> range(start: -30s)
		|> filter(fn: (r) => r._measurement == "node_metrics")
		|> group(columns: ["node", "_field"])
		|> mean()
		`

		result, err := queryAPI.Query(context.Background(), query)
		if err != nil {
			continue
		}

		type NodeScore struct {
			Node  string
			Score float64
		}

		nodeScores := map[string]*NodeScore{}
		for result.Next() {
			node := result.Record().ValueByKey("node").(string)
			field := result.Record().Field()
			value := result.Record().Value().(float64)

			if _, exists := nodeScores[node]; !exists {
				nodeScores[node] = &NodeScore{Node: node}
			}

			fmt.Println(node, field, value)

			switch field {
			case "latency":
				nodeScores[node].Score += value * 0.5
			case "traffic":
				nodeScores[node].Score += value * 0.3
			case "cpu":
				nodeScores[node].Score += value * 0.2
			}
		}

		var sorted []NodeScore
		for _, ns := range nodeScores {
			sorted = append(sorted, *ns)
		}

		sort.Slice(sorted, func(i, j int) bool {
			return sorted[i].Score < sorted[j].Score
		})

		for _, ns := range sorted {
			fmt.Printf("%s %.3f\n", ns.Node, ns.Score)
		}
	}
}

func queryPrometheus(prom v1.API, query string) float64 {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	result, warnings, err := prom.Query(ctx, query, time.Now())
	if err != nil {
		//fmt.Printf("Query failed: %v\n", err)
		return 0
	}
	if len(warnings) > 0 {
		//fmt.Printf("Warnings: %v\n", warnings)
	}

	vector, ok := result.(model.Vector)
	if !ok {
		return 0
	}
	if len(vector) == 0 {
		return 0
	}

	return float64(vector[0].Value)
}

func queryVector(prom v1.API, query string) model.Vector {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	result, _, err := prom.Query(ctx, query, time.Now())

	if err != nil {
		fmt.Printf("Query failed: %v\n", err)
		return nil
	}
	vector, ok := result.(model.Vector)
	if !ok {
		fmt.Printf("Empty result for query: %s\n", query)
		return nil
	}
	return vector
}
