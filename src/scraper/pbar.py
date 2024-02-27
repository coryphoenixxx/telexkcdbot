from rich.progress import MofNCompleteColumn, Progress


class ProgressBar:
    def __init__(self, progress: Progress, desc: str, total: int | None = None):
        self._progress = progress
        self._total = total
        self._task_id = self._progress.add_task(description=desc, total=total)
        self._counter = 0

    def advance(self, step: int = 1):
        self._progress.update(self._task_id, advance=step)
        self._counter += 1

    def finish(self):
        self._progress.stop_task(self._task_id)

        if not self._total:
            col: MofNCompleteColumn = self._progress.columns[-2]

            for task in self._progress.tasks:
                if task.id == self._task_id:
                    task.total = self._counter
                    col.render(task)
