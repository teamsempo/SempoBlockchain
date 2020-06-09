from typing import Optional, NewType, List, Tuple,Callable, Dict

TransferAmount = NewType("TransferAmount", int)

# Executor Jobs consist of the job function, and optionally a list of args and dict of kwargs
ExecutorJob = Tuple[Callable, Optional[List], Optional[Dict]]
ExecutorJobList = List[ExecutorJob]