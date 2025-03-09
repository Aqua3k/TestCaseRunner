import subprocess

# Run pytest with coverage
result = subprocess.run(
    ["pytest", "--junitxml=pytest.xml", "--cov-report=term-missing", "--cov=../src"],
    capture_output=True,
    text=True,
    encoding="utf-8",
)

# Write the coverage report to a file
with open("pytest-coverage.txt", "w") as f:
    f.write(result.stdout)

# Print the output to the console
print(result.stdout)

# Exit with the same return code as pytest
exit(result.returncode)
