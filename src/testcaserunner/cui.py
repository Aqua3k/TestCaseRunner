from rich import print

from .diff_viewer import RunnerLogViewer

def main():
    print("hello.")
    viewer = RunnerLogViewer()
    logs = viewer.get_logs()
    print(logs)
    print(type(logs[0]))
