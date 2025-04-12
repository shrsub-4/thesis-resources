package energyaware

import (
	"context"
	"fmt"
	"time"

	"github.com/prometheus/client_golang/api"
	v1 "github.com/prometheus/client_golang/api/prometheus/v1"
	"github.com/prometheus/common/model"
	"k8s.io/klog/v2"
)

// Prometheus: Queries
const (
	nodeMeasureQueryTemplate = `
		sum_over_time(node_network_receive_bytes_total{instance="%s", device="%s"}[%s])
	`
)

// Handle interaction with Prometheus
type PrometheusHandle struct {
	networkInterface string
	timeRange        time.Duration
	address          string
	api              v1.API
}

func NewPrometheus(address, networkInterface string, timeRange time.Duration) *PrometheusHandle {
	client, err := api.NewClient(api.Config{
		Address: address,
	})
	if err != nil {
		klog.Fatalf("[EnergyAware] Error creating prometheus client: %s", err.Error())
	}

	return &PrometheusHandle{
		networkInterface: networkInterface,
		timeRange:        timeRange,
		address:          address,
		api:              v1.NewAPI(client),
	}
}

func (p *PrometheusHandle) GetNodeBandwidthMeasure(node string) (*model.Sample, error) {
	query := getNodeBandwidthQuery(node, p.networkInterface, p.timeRange)
	klog.Infof("[EnergyAware] Prometheus Query: %s", query)
	res, err := p.query(query)
	if err != nil {
		return nil, fmt.Errorf("[EnergyAware] Error querying prometheus: %w", err)
	}

	nodeMeasure := res.(model.Vector)
	if len(nodeMeasure) != 1 {
		return nil, fmt.Errorf("[EnergyAware] Invalid response, expected 1 value, got %d", len(nodeMeasure))
	}

	return nodeMeasure[0], nil
}

func getNodeBandwidthQuery(node, networkInterface string, timeRange time.Duration) string {
	return fmt.Sprintf(nodeMeasureQueryTemplate, node, networkInterface, timeRange)
}

func (p *PrometheusHandle) query(query string) (model.Value, error) {
	results, warnings, err := p.api.Query(context.Background(), query, time.Now())

	if len(warnings) > 0 {
		klog.Warningf("[EnergyAware] Warnings: %v\n", warnings)
	}

	return results, err
}
