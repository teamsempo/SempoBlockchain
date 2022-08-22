from typing import Optional, NewType, List, Tuple,Callable, Dict

TransferAmount = NewType("TransferAmount", int)

# Deferred Jobs consist of the job function, and optionally a list of args and dict of kwargs
DeferredJob = Tuple[Callable, Optional[List], Optional[Dict]]
DeferredJobList = List[DeferredJob]
