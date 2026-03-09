from typing import Literal

from celery import Task


class BaseTask(Task):
    acks_late = False
    pydantic = True

    def update_progress(
        self,
        state: Literal["STARTED", "PROGRESS", "SUCCESS", "FAILURE"],
        step: int,
        description: str,
        total: int = 4,
        partial_result={},
    ):
        """Function to update progress of task

        Args:
            state (Literal["STARTED", "PROGRESS", "SUCCESS", "FAILURE"]): state of task
            step (int): current step
            description (str): description of task
        """
        # Check if running in Celery context
        try:
            if self.request and self.request.id:
                self.update_state(
                    state=state,
                    meta={
                        "current": step,
                        "total": total,
                        "des": description,
                        "partial_result": partial_result,
                    },
                )
            else:
                # Running outside Celery, just print progress
                print(f"[{state}] Step {step}/{total}: {description}")
        except (AttributeError, RuntimeError):
            # Running outside Celery context, just print progress
            print(f"[{state}] Step {step}/{total}: {description}")
