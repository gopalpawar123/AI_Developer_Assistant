import re
from agents.developer_agent import run_developer_agent
from tools.test_writer import save_generated_test
from tools.test_runner import run_generated_tests, validate_source_path, PROJECT_ROOT
from tools.result_analyzer import analyze_test_result
from tools.test_validator import validate_generated_test
from tools.source_inspector import extract_source_path, inspect_python_source
from tools.test_repair import generate_test_repair, validate_test_repair
from tools.test_repair_diff import generate_repair_diff
from tools.test_repair_saver import save_approved_repair
from tools.test_repair_executor import execute_approved_repair
from tools.repair_history import log_repair_event
MAX_REPAIR_ATTEMPTS = 2
def record_repair_history(filename, event, status, warnings=None, details=None):
    """Record repair activity without interrupting the repair workflow."""
    try:
        log_repair_event(
            filename=filename,
            event=event,
            status=status,
            warnings=warnings,
            details=details,
        )
    except (OSError, ValueError, TypeError) as error:
        print("\nRepair history logging unavailable:", error)
def extract_python_code(response):
    """Extract a Python code block from an AI response."""
    if not isinstance(response, str):
        return None
    match = re.search(
        r"```(?:python|py)[ \t]*\r?\n(.*?)```",
        response,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        return match.group(1).strip() + "\n"
    return None
def is_test_generation_request(user_input):
    """Check whether the user requested test generation."""
    request = user_input.lower()
    return "test" in request and any(
        word in request for word in ["generate", "create", "write"]
    )
def ask_approval(message):
    """Return True only when the user explicitly enters yes."""
    return input(f"\n{message} (yes/no): ").strip().lower() == "yes"
def handle_test_repair(filename, source_path, failure_output):
    """Propose up to two repairs, with separate save and execution approvals."""
    print("\n========== AI TEST REPAIR ==========")
    if not ask_approval("Would you like AI to propose a test repair?"):
        print("\nAI test repair cancelled.")
        return
    if not isinstance(failure_output, str) or not failure_output.strip():
        print("\nNo failure output is available for repair.")
        return
    current_filename = filename
    current_failure = failure_output
    try:
        for attempt in range(1, MAX_REPAIR_ATTEMPTS + 1):
            print(f"\nAI repair attempt {attempt}/{MAX_REPAIR_ATTEMPTS}")
            record_repair_history(
                filename=current_filename,
                event="repair_attempt_started",
                status="started",
                details={
                    "attempt": attempt,
                    "max_attempts": MAX_REPAIR_ATTEMPTS,
                },
            )
            print("\nAI Assistant: Generating repair proposal...")
            proposal = generate_test_repair(
                source_path, current_filename, current_failure
            )
            if isinstance(proposal, dict):
                if proposal.get("status") != "success":
                    print("\nRepair generation failed:", proposal.get("output", "Unknown error"))
                    return
                ai_response = proposal.get("output", "")
            elif isinstance(proposal, str):
                ai_response = proposal
            else:
                print("\nUnexpected repair response format.")
                return
            if not isinstance(ai_response, str) or not ai_response.strip():
                print("\nAI returned an empty repair proposal.")
                return
            print("\n========== RAW AI REPAIR RESPONSE ==========")
            print(ai_response)
            print("============================================")
            print("\nValidating the AI-generated repair...")
            # Compare against the exact test file currently being repaired.
            if (
                not isinstance(current_filename, str)
                or not current_filename.startswith("test_")
                or not current_filename.endswith(".py")
                or "/" in current_filename
                or "\\" in current_filename
            ):
                print("\nInvalid test filename for quality validation.")
                return
            test_file = PROJECT_ROOT / "generated_tests" / current_filename
            if test_file.is_symlink() or not test_file.is_file():
                print("\nMissing or unsafe test file for quality validation.")
                return
            original_test_code = test_file.read_text(encoding="utf-8")
            validation = validate_test_repair(
                ai_response,
                source_path,
                original_test_code=original_test_code,
            )
            if not isinstance(validation, dict):
                print("\nUnexpected repair validation result.")
                return
            record_repair_history(
                filename=current_filename,
                event="repair_validation",
                status="passed" if validation.get("valid", False) else "failed",
                warnings=validation.get("warnings") or [],
                details={
                    "attempt": attempt,
                    "error_count": len(validation.get("errors") or []),
                },
            )
            if not validation.get("valid", False):
                print("\nRepair validation failed.")
                for error in validation.get("errors", []):
                    print("-", error)
                return
            quality_warnings = validation.get("warnings", [])
            for warning in quality_warnings:
                print("Repair quality warning:", warning)
            repaired_code = validation.get("code")
            if not isinstance(repaired_code, str) or not repaired_code.strip():
                print("\nValidated repair code is missing.")
                return
            print("\nComparing original and repaired tests...")
            diff_result = generate_repair_diff(current_filename, repaired_code)
            if not isinstance(diff_result, dict) or diff_result.get("status") != "success":
                print("\nUnable to generate repair diff:",
                      diff_result.get("output", "Unknown error") if isinstance(diff_result, dict) else "Unexpected response")
                return
            if not diff_result.get("changed"):
                print("\nAI did not propose any code changes.")
                return
            print("\n========== PROPOSED REPAIR DIFF ==========")
            print(diff_result["diff"])
            print("==========================================")
            print("\nReview the proposed changes carefully."
                  "\nThe original test file will not be overwritten.")
            if quality_warnings:
                print("\nWARNING: This repair may reduce test coverage.")
                warnings_accepted = ask_approval(
                    "Do you explicitly accept the quality warnings?"
                )
                record_repair_history(
                    filename=current_filename,
                    event="quality_warning_approval",
                    status="accepted" if warnings_accepted else "rejected",
                    warnings=quality_warnings,
                    details={"attempt": attempt},
                )
                if not warnings_accepted:
                    print("\nRepair rejected due to quality warnings.")
                    return
            save_approved = ask_approval(
                "Do you approve saving this repaired test?"
            )
            record_repair_history(
                filename=current_filename,
                event="repair_save_approval",
                status="approved" if save_approved else "rejected",
                details={"attempt": attempt},
            )
            if not save_approved:
                print("\nRepair saving cancelled.")
                return
            save_result = save_approved_repair(
                current_filename, repaired_code, approved=True
            )
            if not isinstance(save_result, dict):
                print("\nUnexpected repair saving result.")
                return
            print("\n", save_result.get("output", ""))
            if save_result.get("status") != "success":
                print("\nUnable to save repaired test.")
                return
            repaired_filename = save_result["filename"]
            print("\nRepaired test saved:", repaired_filename)
            docker_approved = ask_approval(
                "Do you approve executing the repaired test in Docker?"
            )
            record_repair_history(
                filename=repaired_filename,
                event="repair_docker_approval",
                status="approved" if docker_approved else "rejected",
                details={"attempt": attempt},
            )
            if not docker_approved:
                print("\nRepaired test execution cancelled.")
                return
            print("\nExecuting repaired tests inside Docker...")
            execution_result = execute_approved_repair(
                repaired_filename, source_path, approved=True
            )
            if not isinstance(execution_result, dict):
                print("\nUnexpected Docker execution result.")
                return
            status = execution_result.get("status", "unknown")
            output = execution_result.get("output", "")
            record_repair_history(
                filename=repaired_filename,
                event="repair_docker_execution",
                status=status,
                details={"attempt": attempt},
            )
            print("\n========== REPAIR EXECUTION RESULT ==========")
            print("Status:", str(status).upper())
            print(output)
            print("=============================================")
            if status == "passed":
                print("\nRepaired tests passed successfully.")
                return
            if status == "failed":
                print("\nRepaired tests are still failing.")
                if attempt == MAX_REPAIR_ATTEMPTS:
                    print("\nMaximum repair attempts reached. Review the failures manually.")
                    return
                if not isinstance(output, str) or not output.strip():
                    print("\nNo Docker failure details available for another repair.")
                    return
                retry_approved = ask_approval(
                   "Would you like AI to attempt another repair?"
                )
                record_repair_history(
                    filename=repaired_filename,
                    event="repair_retry_approval",
                    status="approved" if retry_approved else "rejected",
                    details={
                        "attempt": attempt,
                        "next_attempt": attempt + 1,
                    },
                )
                if not retry_approved:
                    print("\nAdditional repair cancelled.")
                    return
                current_filename = repaired_filename
                current_failure = output
                continue
            if status == "timeout":
                print("\nRepaired test execution timed out.")
            else:
                print("\nRepaired test execution was unsuccessful.")
            return
    except (KeyboardInterrupt, EOFError):
        raise
    except Exception as error:
        print("\nAI test repair unavailable:", error)
def handle_test_execution(filename, source_path):
    """Request approval and execute generated tests in Docker."""
    print("\nThe generated test file has been saved.")
    source_file = validate_source_path(source_path)
    if source_file is None:
        print("\nDocker execution is unavailable for this source file.")
        print("Only existing Python source files inside the approved examples directory are supported.")
        return
    print("\nSource file:", source_path)
    print("Docker execution is available for this source.")
    if not ask_approval("Would you like to execute these tests in Docker?"):
        print("\nTest execution cancelled.")
        return
    print("\nExecuting tests inside Docker...")
    result = run_generated_tests(filename, approved=True, source_path=source_path)
    status = result.get("status", "unknown")
    output = result.get("output", "")
    print("\n========== TEST EXECUTION RESULT ==========")
    print("Status:", str(status).upper())
    print(output)
    print("===========================================")
    if status == "failed":
        if ask_approval("Would you like AI to analyze the failure?"):
            print("\nAI Assistant: Analyzing test failure...")
            try:
                analysis = analyze_test_result(result)
                print("\n========== AI FAILURE ANALYSIS ==========")
                print(analysis)
                print("=========================================")
            except Exception as error:
                print("\nAI failure analysis unavailable:", error)
        handle_test_repair(filename, source_path, output)
    elif status == "passed":
        print("\nAll generated tests passed successfully.")
    elif status == "timeout":
        print("\nTest execution timed out.")
    elif status == "error":
        print("\nUnable to execute the generated tests.")
    elif status == "rejected":
        print("\nTest execution was rejected.")
def main():
    """Start the AI Developer Assistant CLI."""
    print("======================================")
    print("       AI DEVELOPER ASSISTANT")
    print("======================================")
    print("Model: Qwen 2.5 3B")
    print("\nAvailable tools:")
    for tool in [
        "File Reader", "Code Analyzer", "Unit Test Generator", "Test File Writer",
        "Source-Aware Test Validator", "Dynamic Docker Test Runner",
        "AI Failure Analyzer", "AI Test Repair Generator",
        "Repair Validation and Diff", "Approved Repair Saving",
        "Approved Docker Re-execution", "Approved Repair Retry (max 2 attempts)",
    ]:
        print("-", tool)
    print("\nType 'exit' to close.")
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() == "exit":
                print("\nAI Assistant: Goodbye!")
                break
            if not user_input:
                continue
            print("\nAI Assistant: Processing...")
            response = run_developer_agent(user_input)
            print("\nAI Assistant:\n", response)
            if not is_test_generation_request(user_input):
                continue
            source_path = extract_source_path(user_input)
            if not source_path:
                print("\nUnable to identify a Python source file in the request.")
                continue
            source_info = inspect_python_source(source_path)
            if not source_info["valid"]:
                print("\nSource inspection failed:", source_info["error"])
                continue
            print("\nSource module:", source_info["module"])
            print("Available functions:", source_info["functions"])
            code = extract_python_code(response)
            if not code:
                print("\nNo Python test code found in the response.")
                continue
            print("\nValidating generated test code...")
            validation = validate_generated_test(
                code,
                required_imports=source_info["functions"],
                source_module=source_info["module"],
            )
            if not validation["valid"]:
                print("\nGenerated test validation failed:")
                for error in validation["errors"]:
                    print("-", error)
                print("\nPlease regenerate or correct the tests.")
                continue
            if validation.get("warnings"):
                print("\nValidation warnings:")
                for warning in validation["warnings"]:
                    print("-", warning)
                print("\nReview these warnings before saving.")
            print("\nGenerated test validation passed.")
            print("\nReview the generated code above before saving.")
            if not ask_approval("Would you like to save the generated tests?"):
                print("\nSaving cancelled.")
                continue
            filename = input("Enter filename (e.g. test_ai_calculator.py): ").strip()
            save_result = save_generated_test(filename, code)
            print("\n", save_result)
            if not save_result.startswith("Saved successfully:"):
                continue
            handle_test_execution(filename, source_path)
        except (KeyboardInterrupt, EOFError):
            print("\nAI Assistant: Goodbye!")
            break
        except Exception as error:
            print("\nApplication error:", error)
if __name__ == "__main__":
    main()
