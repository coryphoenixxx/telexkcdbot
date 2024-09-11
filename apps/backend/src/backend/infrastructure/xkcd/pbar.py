from rich.progress import MofNCompleteColumn, Progress


class CustomProgressBar:
    def __init__(self, progress: Progress, desc: str, total: int | None = None) -> None:
        self._progress = progress
        self._total = total
        self._task_id = self._progress.add_task(description=desc, total=total)
        self._counter = 0

    def advance(self, step: int = 1) -> None:
        self._progress.update(self._task_id, advance=step)
        self._counter += 1

    def finish(self) -> None:
        self._progress.stop_task(self._task_id)

        if not self._total:
            column = self._progress.columns[-2]

            if isinstance(column, MofNCompleteColumn):
                for task in self._progress.tasks:
                    if task.id == self._task_id:
                        task.total = self._counter
                        column.render(task)
