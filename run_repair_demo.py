
from tools.test_runner import run_generated_tests
from app import handle_test_repair


def main():
    source_path = "examples/string_utils.py"
    test_filename = "test_retry_scenario.py"

    print("\nRunning initial test in Docker...")

    result = run_generated_tests(
        test_filename,
        approved=True,
        source_path=source_path,
    )

    print("\n========== INITIAL TEST RESULT ==========")
    print("Status:", result["status"].upper())
    print(result["output"])
    print("=========================================")

    if result["status"] == "failed":
        handle_test_repair(
            test_filename,
            source_path,
            result["output"],
        )
    else:
        print("\nNo repair needed or execution did not fail.")


if __name__ == "__main__":
    main()
