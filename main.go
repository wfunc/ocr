package main

import (
	"bytes"
	"context"
	"errors"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
)

const defaultCommandTimeout = 30 * time.Second

var (
	scriptPath string
	pythonExec string
)

func init() {
	path, err := filepath.Abs("ocr.py")
	if err != nil {
		log.Fatalf("failed to resolve path to ocr.py: %v", err)
	}
	scriptPath = path

	pythonExec = strings.TrimSpace(os.Getenv("PYTHON_BIN"))
	if pythonExec == "" {
		pythonExec = "python3"
	}
}

type ocrRequest struct {
	URL string `json:"url"`
}

func main() {
	if _, err := os.Stat(scriptPath); err != nil {
		log.Fatalf("ocr.py not found at %s: %v", scriptPath, err)
	}

	if _, err := exec.LookPath(pythonExec); err != nil {
		log.Fatalf("python interpreter '%s' not found in PATH (override with PYTHON_BIN)", pythonExec)
	}

	router := gin.Default()
	router.GET("/ocr", ocrHandler)
	router.POST("/ocr", ocrHandler)

	if err := router.Run(":3844"); err != nil {
		log.Fatalf("failed to start server: %v", err)
	}
}

func ocrHandler(c *gin.Context) {
	input := strings.TrimSpace(c.Query("url"))
	if input == "" && c.Request.Method == http.MethodPost {
		var req ocrRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid JSON payload", "details": err.Error()})
			return
		}
		input = strings.TrimSpace(req.URL)
	}

	if input == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "missing url parameter"})
		return
	}

	result, rawOutput, err := runOCR(c.Request.Context(), input)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":      err.Error(),
			"raw_output": rawOutput,
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"result": result,
		// "raw_output": rawOutput,
	})
}

func runOCR(parent context.Context, input string) (string, string, error) {
	ctx, cancel := context.WithTimeout(parent, defaultCommandTimeout)
	defer cancel()

	cmd := exec.CommandContext(ctx, pythonExec, scriptPath, input)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		if errors.Is(ctx.Err(), context.DeadlineExceeded) {
			return "", stdout.String(), errors.New("ocr script timed out")
		}
		if stderr.Len() > 0 {
			return "", stdout.String(), errors.New(strings.TrimSpace(stderr.String()))
		}
		return "", stdout.String(), err
	}

	rawOutput := stdout.String()
	result := extractResult(rawOutput)
	if result == "" {
		return "", rawOutput, errors.New("ocr script returned empty result")
	}
	return result, rawOutput, nil
}

// extractResult returns the last non-empty line from the script output.
func extractResult(output string) string {
	lines := strings.Split(output, "\n")
	for i := len(lines) - 1; i >= 0; i-- {
		line := strings.TrimSpace(lines[i])
		if line != "" {
			return line
		}
	}
	return ""
}
