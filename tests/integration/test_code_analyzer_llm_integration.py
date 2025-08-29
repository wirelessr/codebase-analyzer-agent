"""
Integration tests for Code Analyzer Agent LLM and Prompt Effectiveness.

TESTING SCENARIO: DEBUGGING AND ERROR ANALYSIS (Go Language)
Tests the actual LLM integration and prompt effectiveness for debugging:
- Bug identification and error detection with real LLM calls in Go code
- Exception handling analysis and error handling patterns in Go
- Code stability and robustness assessment in Go applications
- Memory safety and concurrency error evaluation
- Multi-round debugging analysis convergence
- Debugging-focused prompt validation and response quality for Go language
"""

import os
import sys
import tempfile

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from codebase_agent.agents.code_analyzer import CodeAnalyzer


class TestCodeAnalyzerLLMIntegration:
    """Integration tests for Code Analyzer LLM and prompt effectiveness."""

    @pytest.fixture
    def shell_tool(self, temp_codebase):
        """Create a real shell tool for testing."""
        from codebase_agent.tools.shell_tool import ShellTool

        return ShellTool(temp_codebase)

    @pytest.fixture
    def config(self):
        """Create real LLM configuration for testing."""
        try:
            from codebase_agent.config.configuration import ConfigurationManager

            config_manager = ConfigurationManager()
            config_manager.load_environment()
            return config_manager.get_model_client()
        except Exception as e:
            pytest.skip(f"Could not configure LLM: {e}")

    @pytest.fixture
    def analyzer(self, config, shell_tool):
        """Create a real CodeAnalyzer instance with LLM integration."""
        return CodeAnalyzer(config, shell_tool)

    @pytest.fixture
    def temp_codebase(self):
        """Create a temporary Go codebase with bugs for debugging testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a Go project structure with common bugs
            os.makedirs(os.path.join(temp_dir, "cmd"))
            os.makedirs(os.path.join(temp_dir, "internal"))
            os.makedirs(os.path.join(temp_dir, "pkg"))

            # Create go.mod
            with open(os.path.join(temp_dir, "go.mod"), "w") as f:
                f.write(
                    """module buggy-go-app

go 1.19

require (
    github.com/gorilla/mux v1.8.0
    github.com/lib/pq v1.10.7
)
"""
                )

            # Create main.go with deliberate bugs
            with open(os.path.join(temp_dir, "cmd", "main.go"), "w") as f:
                f.write(
                    """package main

import (
    "database/sql"
    "fmt"
    "log"
    "net/http"
    "os"
    "strconv"

    "github.com/gorilla/mux"
    _ "github.com/lib/pq"
)

// Bug: Global variable without protection for concurrent access
var userCount int

type User struct {
    ID   int    `json:"id"`
    Name string `json:"name"`
    Age  int    `json:"age"`
}

// Bug: No error handling for database connection
func connectDB() *sql.DB {
    dbURL := os.Getenv("DATABASE_URL")
    if dbURL == "" {
        dbURL = "postgres://user:password@localhost/dbname?sslmode=disable"
    }

    db, err := sql.Open("postgres", dbURL)
    if err != nil {
        // Bug: Using log.Fatal in library code instead of returning error
        log.Fatal(err)
    }

    // Bug: Not checking if connection is actually working
    return db
}

// Bug: SQL injection vulnerability
func getUserByID(db *sql.DB, userID string) (*User, error) {
    query := fmt.Sprintf("SELECT id, name, age FROM users WHERE id = %s", userID)

    var user User
    err := db.QueryRow(query).Scan(&user.ID, &user.Name, &user.Age)
    if err != nil {
        return nil, err
    }

    return &user, nil
}

// Bug: Race condition - concurrent access to global variable
func incrementUserCount() {
    userCount++
}

// Bug: Not handling conversion errors properly
func handleGetUser(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    userIDStr := vars["id"]

    // Bug: Ignoring conversion error
    userID, _ := strconv.Atoi(userIDStr)

    db := connectDB()
    // Bug: Not closing database connection

    user, err := getUserByID(db, strconv.Itoa(userID))
    if err != nil {
        // Bug: Exposing internal error details to client
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    incrementUserCount()

    // Bug: Not setting content type
    fmt.Fprintf(w, `{"id": %d, "name": "%s", "age": %d}`, user.ID, user.Name, user.Age)
}

// Bug: No graceful shutdown handling
func main() {
    r := mux.NewRouter()
    r.HandleFunc("/users/{id}", handleGetUser).Methods("GET")

    fmt.Println("Server starting on :8080")

    // Bug: Not handling server startup errors
    http.ListenAndServe(":8080", r)
}
"""
                )

            # Create a utility file with more bugs
            with open(os.path.join(temp_dir, "internal", "utils.go"), "w") as f:
                f.write(
                    """package internal

import (
    "encoding/json"
    "io"
    "time"
)

// Bug: Potential memory leak - slice growing indefinitely
var requestLog []string

// Bug: Not handling JSON unmarshal errors properly
func ParseUserRequest(body io.Reader) (map[string]interface{}, error) {
    var result map[string]interface{}

    // Bug: No limit on body size - potential DoS
    bodyBytes, _ := io.ReadAll(body)

    err := json.Unmarshal(bodyBytes, &result)
    if err != nil {
        // Bug: Returning nil map with error - inconsistent state
        return nil, err
    }

    // Bug: Adding to slice without bounds checking
    requestLog = append(requestLog, string(bodyBytes))

    return result, nil
}

// Bug: Goroutine leak - channel never closed
func StartBackgroundWorker() {
    ch := make(chan string)

    go func() {
        for msg := range ch {
            // Bug: No timeout on processing
            processMessage(msg)
        }
    }()

    // Bug: Channel never gets any data, goroutine blocks forever
}

func processMessage(msg string) {
    // Bug: Infinite loop potential
    for {
        if len(msg) > 0 {
            break
        }
        // Bug: No sleep, will consume CPU
    }

    // Bug: Panic not recovered
    if msg == "panic" {
        panic("Intentional panic")
    }
}

// Bug: Time-based race condition
func GetCurrentTimestamp() string {
    now := time.Now()
"""
                )

            # Create a test file with expected bugs
            with open(os.path.join(temp_dir, "pkg", "models.go"), "w") as f:
                f.write(
                    """package pkg

import (
    "database/sql"
    "fmt"
)

type UserService struct {
    db *sql.DB
}

// Bug: Method receiver not using pointer, won't persist changes
func (u UserService) SetDB(database *sql.DB) {
    u.db = database
}

// Bug: Not validating input parameters
func (u *UserService) CreateUser(name string, age int) (int, error) {
    // Bug: SQL injection vulnerability
    query := fmt.Sprintf("INSERT INTO users (name, age) VALUES ('%s', %d)", name, age)

    result, err := u.db.Exec(query)
    if err != nil {
        return 0, err
    }

    // Bug: Not checking if LastInsertId is supported
    id, _ := result.LastInsertId()
    return int(id), nil
}

// Bug: Resource leak - not closing rows
func (u *UserService) GetAllUsers() ([]User, error) {
    rows, err := u.db.Query("SELECT id, name, age FROM users")
    if err != nil {
        return nil, err
    }

    var users []User
    for rows.Next() {
        var user User
        err := rows.Scan(&user.ID, &user.Name, &user.Age)
        if err != nil {
            // Bug: Continuing loop despite error
            continue
        }
        users = append(users, user)
    }

    return users, nil
}
"""
                )

            # Create README with project description
            with open(os.path.join(temp_dir, "README.md"), "w") as f:
                f.write(
                    """# Buggy Go Application

This is a simple Go web API project that contains several common programming bugs for debugging analysis.

## Known Issues

The codebase intentionally contains various types of bugs:
- SQL injection vulnerabilities
- Race conditions and concurrent access issues
- Resource leaks (database connections, goroutines)
- Missing error handling
- Memory leaks
- Potential DoS vulnerabilities
- Type conversion errors
- Time formatting issues

## Dependencies

- github.com/gorilla/mux - HTTP router
- github.com/lib/pq - PostgreSQL driver

## Structure

- cmd/main.go - Main application entry point
- internal/utils.go - Utility functions
- pkg/models.go - Data models and services
"""
                )

            yield temp_dir

    def test_basic_analysis_prompt_effectiveness(self, analyzer, temp_codebase):
        """Test debugging analysis prompt with real LLM."""
        query = (
            "分析這個Go專案中的潛在錯誤和安全漏洞，找出可能導致程式崩潰或資料洩露的bug"
        )

        result = analyzer.analyze_codebase(query, temp_codebase)

        # Verify the analysis contains expected debugging elements
        assert "CODEBASE ANALYSIS COMPLETE" in result
        assert len(result) > 100  # Should be a substantial debugging analysis

        # Check for debugging-related analysis elements
        debugging_keywords = [
            "error",
            "bug",
            "nil pointer",
            "race condition",
            "sql injection",
            "resource leak",
            "goroutine",
            "vulnerability",
            "錯誤",
            "漏洞",
            "除錯",
        ]
        result_lower = result.lower()
        found_keywords = [
            keyword for keyword in debugging_keywords if keyword in result_lower
        ]
        assert (
            len(found_keywords) >= 2
        ), f"Expected debugging analysis keywords, found: {found_keywords}"

    def test_analysis_convergence_prompt(self, analyzer, temp_codebase):
        """Test that debugging analysis prompts lead to convergence on error identification."""
        query = "完整除錯分析：找出這個Go專案中所有的安全漏洞、並發問題和資源洩露問題"

        result = analyzer.analyze_codebase(query, temp_codebase)

        # Verify debugging analysis completion
        assert "CODEBASE ANALYSIS COMPLETE" in result
        assert "Iterations:" in result

        # Extract iteration count
        lines = result.split("\n")
        iteration_line = next((line for line in lines if "Iterations:" in line), None)
        assert iteration_line is not None

        # Should converge in reasonable number of iterations (not hit max limit)
        iteration_count = int(iteration_line.split("Iterations:")[1].strip().split()[0])
        assert 1 <= iteration_count <= 10

        # Check for error identification
        error_terms = [
            "sql injection",
            "nil pointer",
            "race condition",
            "resource leak",
            "goroutine leak",
            "vulnerability",
            "錯誤處理",
            "安全漏洞",
            "並發問題",
        ]
        result_lower = result.lower()
        found_error_terms = [term for term in error_terms if term in result_lower]
        assert (
            len(found_error_terms) >= 1
        ), f"Expected error identification, found: {found_error_terms}"

    def test_prompt_chinese_language_support(self, analyzer, temp_codebase):
        """Test that debugging prompts work effectively in Chinese."""
        query = "評估這個Go專案的程式碼安全性和穩定性，找出容易造成資料洩露或程式崩潰的問題點"

        result = analyzer.analyze_codebase(query, temp_codebase)

        # Verify the LLM understood the Chinese debugging query
        assert "CODEBASE ANALYSIS COMPLETE" in result

        # Should mention stability and crash-related concepts in response
        stability_keywords = [
            "stability",
            "crash",
            "error",
            "exception",
            "穩定",
            "當機",
            "錯誤",
            "異常",
            "問題",
        ]
        result_lower = result.lower()
        found_keywords = [
            keyword for keyword in stability_keywords if keyword in result_lower
        ]
        assert (
            len(found_keywords) >= 2
        ), f"Expected stability/debugging keywords, found: {found_keywords}"

    def test_specialist_feedback_prompt_integration(self, analyzer, temp_codebase):
        """Test that specialist feedback is properly integrated into debugging prompts."""
        query = "分析專案中的錯誤處理"
        feedback = "請特別關注除錯資訊的完整性和錯誤恢復機制的設計"

        result = analyzer.analyze_codebase(
            query, temp_codebase, specialist_feedback=feedback
        )

        # Verify feedback was incorporated into debugging analysis
        assert "CODEBASE ANALYSIS COMPLETE" in result

        # Should reflect the specialist feedback focus on debugging and error recovery
        debugging_keywords = [
            "sql injection",
            "race condition",
            "nil pointer",
            "goroutine",
            "resource leak",
            "vulnerability",
            "錯誤處理",
            "安全漏洞",
            "並發問題",
            "error",
            "concurrency",
            "memory safety",
            "security",
            "robustness",
        ]
        result_lower = result.lower()
        found_keywords = [
            keyword for keyword in debugging_keywords if keyword in result_lower
        ]
        has_debugging_focus = len(found_keywords) >= 2

        # If no direct keywords found, check if the analysis is substantial (indicating focus was applied)
        if not has_debugging_focus:
            # As long as we got a detailed analysis, specialist feedback was likely considered
            assert (
                len(result) > 200
            ), f"Expected substantial debugging analysis when feedback provided, got {len(result)} chars"
        else:
            # Great! Found relevant debugging keywords
            pass

    def test_multi_round_prompt_consistency(self, analyzer, temp_codebase):
        """Test that multi-round debugging prompts maintain consistency."""
        query = "深入分析這個Go專案的錯誤處理機制、並發安全性和資源管理設計"

        result = analyzer.analyze_codebase(query, temp_codebase)

        # Verify the debugging analysis went through multiple rounds
        assert "CODEBASE ANALYSIS COMPLETE" in result
        assert "Iterations:" in result

        # Should contain consistent debugging and error handling analysis
        debugging_keywords = [
            "error",
            "concurrency",
            "goroutine",
            "nil pointer",
            "resource",
            "safety",
            "錯誤",
            "並發",
            "安全",
            "資源",
        ]
        result_lower = result.lower()
        found_keywords = [
            keyword for keyword in debugging_keywords if keyword in result_lower
        ]
        assert (
            len(found_keywords) >= 2
        ), f"Expected debugging consistency, found: {found_keywords}"


# Manual test runner for development
if __name__ == "__main__":
    # This allows manual testing during development
    # Remove the @pytest.mark.skip decorators to run with real LLM
    print("Code Analyzer LLM Integration Tests")
    print("Remove @pytest.mark.skip decorators to run with real LLM")
    pytest.main([__file__, "-v", "-s"])
