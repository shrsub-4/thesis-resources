package main

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/prometheus/client_golang/api"
	promv1 "github.com/prometheus/client_golang/api/prometheus/v1"
	"github.com/prometheus/common/model"
)

const (
	prometheusURL    = "http://10.104.0.94:32582/"
	nodeExporterURL  = "http://10.104.0.94:9100/metrics"
	metricsServerURL = "https://10.104.0.94:30415/apis/metrics.k8s.io/v1beta1/pods"
)

type RollingMetrics struct {
	latency []float64
	errors  []float64
	cpu     []float64
	memory  []float64
}

var metrics RollingMetrics

func main() {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		collectMetrics()
		displayMetrics()
	}
}

func collectMetrics() {
	var wg sync.WaitGroup
	wg.Add(3)

	go func() {
		defer wg.Done()
		fetchIstioMetrics()
	}()

	go func() {
		defer wg.Done()
		fetchNodeExporterMetrics()
	}()

	go func() {
		defer wg.Done()
		fetchMetricsServerData()
	}()

	wg.Wait()
}

func fetchIstioMetrics() {
	client, err := api.NewClient(api.Config{Address: prometheusURL})
	if err != nil {
		log.Printf("Error creating Prometheus client: %v", err)
		return
	}

	v1api := promv1.NewAPI(client)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	queryLatency := `histogram_quantile(0.95, sum(rate(istio_request_duration_milliseconds_bucket[5m])) by (le))`
	resultLatency, _, err := v1api.Query(ctx, queryLatency, time.Now())
	if err == nil {
		storeRollingAverage(&metrics.latency, extractFloat(resultLatency))
	}

	queryErrors := `rate(istio_requests_total{response_code=~"5.."}[5m])`
	resultErrors, _, err := v1api.Query(ctx, queryErrors, time.Now())
	if err == nil {
		storeRollingAverage(&metrics.errors, extractFloat(resultErrors))
	}
}

func fetchNodeExporterMetrics() {
	client, err := api.NewClient(api.Config{Address: prometheusURL})
	if err != nil {
		log.Printf("Error creating Prometheus client: %v", err)
		return
	}

	v1api := promv1.NewAPI(client)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	queryCPU := `100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)`
	resultCPU, _, err := v1api.Query(ctx, queryCPU, time.Now())
	if err == nil {
		storeRollingAverage(&metrics.cpu, extractFloat(resultCPU))
	}

	queryMemory := `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`
	resultMemory, _, err := v1api.Query(ctx, queryMemory, time.Now())
	if err == nil {
		storeRollingAverage(&metrics.memory, extractFloat(resultMemory))
	}
}

func fetchMetricsServerData() {
	http.DefaultTransport.(*http.Transport).TLSClientConfig = &tls.Config{InsecureSkipVerify: true}

	resp, err := http.Get(metricsServerURL)
	if err != nil {
		log.Printf("Error fetching metrics-server data: %v", err)
		return
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Error reading response body: %v", err)
		return
	}

	var metricsData struct {
		Items []struct {
			Metadata struct {
				Name      string `json:"name"`
				Namespace string `json:"namespace"`
			} `json:"metadata"`
			Containers []struct {
				Name  string `json:"name"`
				Usage struct {
					CPU    string `json:"cpu"`
					Memory string `json:"memory"`
				} `json:"usage"`
			} `json:"containers"`
		} `json:"items"`
	}

	err = json.Unmarshal(body, &metricsData)
	if err != nil {
		log.Printf("Error parsing JSON: %v", err)
		return
	}

	var totalCPU, totalMemory float64
	for _, item := range metricsData.Items {
		for _, container := range item.Containers {
			totalCPU += parseCPU(container.Usage.CPU)
			totalMemory += parseMemory(container.Usage.Memory)
		}
	}

	storeRollingAverage(&metrics.cpu, totalCPU)
	storeRollingAverage(&metrics.memory, totalMemory)
}

func displayMetrics() {
	fmt.Println("Metrics Summary:")
	fmt.Printf("Request Latency: %.2f ms\n", getRollingAverage(metrics.latency))
	fmt.Printf("Error Rate: %.4f errors/sec\n", getRollingAverage(metrics.errors))
	fmt.Printf("CPU Usage: %.2f%%\n", getRollingAverage(metrics.cpu))
	fmt.Printf("Memory Usage: %.2f%%\n", getRollingAverage(metrics.memory))
}

func storeRollingAverage(slice *[]float64, value float64) {
	*slice = append(*slice, value)
	if len(*slice) > 6 {
		*slice = (*slice)[1:]
	}
}

func getRollingAverage(slice []float64) float64 {
	if len(slice) == 0 {
		return 0.0
	}
	sum := 0.0
	for _, v := range slice {
		sum += v
	}
	return sum / float64(len(slice))
}

func extractFloat(result model.Value) float64 {
	switch v := result.(type) {
	case model.Vector:
		if len(v) > 0 {
			return float64(v[0].Value)
		}
	case *model.Scalar:
		return float64(v.Value)
	}
	return 0.0
}

func parseCPU(cpuStr string) float64 {
	if strings.HasSuffix(cpuStr, "n") {
		value, _ := strconv.ParseFloat(strings.TrimSuffix(cpuStr, "n"), 64)
		return value / 1_000_000_000
	}
	return 0.0
}

func parseMemory(memStr string) float64 {
	if strings.HasSuffix(memStr, "Ki") {
		value, _ := strconv.ParseFloat(strings.TrimSuffix(memStr, "Ki"), 64)
		return value / 1024
	}
	return 0.0
}
