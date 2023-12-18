import os
from typing import Union
from .dev_config import DevConfig
from .prod_config import ProdConfig

ENV = os.getenv('ENV', 'development')

# Instantiate the appropriate config class based on the environment
CurrentConfig: Union[DevConfig, ProdConfig] = DevConfig() if ENV == 'development' else ProdConfig()
