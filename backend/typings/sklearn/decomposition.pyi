from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

class PCA:
    def __init__(self, n_components: int, random_state: int) -> None: ...
    def fit_transform(self, values: Sequence[object]) -> npt.NDArray[np.float64]: ...
