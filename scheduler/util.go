package energyaware

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	v1 "k8s.io/api/core/v1"
	framework "k8s.io/kubernetes/pkg/scheduler/framework"
)

func getInternalIP(node *v1.Node) (string, error) {
	for _, addr := range node.Status.Addresses {
		if addr.Type == v1.NodeInternalIP {
			return addr.Address, nil
		}
	}
	return "", fmt.Errorf("[EnergyAware] no internal IP found for node %s", node.Name)
}

// queryOptimizer contacts the external service and gets a node recommendation
func queryOptimizer(optimizerURL string, pod *v1.Pod, nodes []*framework.NodeInfo) (string, error) {
	type OptimizerRequest struct {
		Pod   string   `json:"pod"`
		Nodes []string `json:"nodes"`
	}
	type OptimizerResponse struct {
		Node string `json:"node"`
	}

	// Prepare request
	nodeNames := make([]string, len(nodes))
	for i, n := range nodes {
		nodeNames[i] = n.Node().Name
	}

	requestBody, _ := json.Marshal(OptimizerRequest{
		Pod:   pod.Name,
		Nodes: nodeNames,
	})

	resp, err := http.Post(optimizerURL+"/optimize", "application/json", io.NopCloser(bytes.NewReader(requestBody)))
	if err != nil {
		return "", fmt.Errorf("failed to query optimizer: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("optimizer returned non-200: %d", resp.StatusCode)
	}

	var result OptimizerResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", fmt.Errorf("failed to decode optimizer response: %w", err)
	}

	return result.Node, nil
}
