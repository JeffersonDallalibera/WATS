"""Simple Dependency Injection container for WATS application."""

import inspect
import logging
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, get_type_hints
from functools import wraps

T = TypeVar('T')


class DIContainer:
    """
    Container simples para Dependency Injection.
    
    Permite registro e resolução automática de dependências, suportando:
    - Singletons e instâncias transientes
    - Factory functions
    - Resolução automática de dependências via type hints
    - Decorators para injeção automática
    """
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}
        self._transient_types: set = set()
        
    def register(
        self,
        interface: Type[T],
        implementation: Union[Type[T], Callable[..., T], T],
        singleton: bool = True
    ) -> 'DIContainer':
        """
        Registra um serviço no container.
        
        Args:
            interface: Tipo/interface do serviço
            implementation: Implementação, factory ou instância
            singleton: Se deve manter instância única
            
        Returns:
            Self para chaining
            
        Examples:
            >>> container.register(IUserRepository, UserRepository)
            >>> container.register(ILogger, lambda: FileLogger("app.log"))
            >>> container.register(str, "my_config_value", singleton=False)
        """
        if inspect.isclass(implementation):
            # Classe - será instanciada quando necessário
            self._services[interface] = implementation
            if not singleton:
                self._transient_types.add(interface)
        elif callable(implementation):
            # Factory function
            self._factories[interface] = implementation
            if not singleton:
                self._transient_types.add(interface)
        else:
            # Instância já criada
            self._services[interface] = implementation
            if singleton:
                self._singletons[interface] = implementation
        
        logging.debug(f"Registrado: {interface.__name__} -> {implementation}")
        return self
    
    def register_singleton(self, interface: Type[T], implementation: Union[Type[T], T]) -> 'DIContainer':
        """Registra um serviço como singleton."""
        return self.register(interface, implementation, singleton=True)
    
    def register_transient(self, interface: Type[T], implementation: Union[Type[T], Callable[..., T]]) -> 'DIContainer':
        """Registra um serviço como transient (nova instância a cada resolução)."""
        return self.register(interface, implementation, singleton=False)
    
    def register_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """Registra uma instância específica."""
        self._singletons[interface] = instance
        logging.debug(f"Instância registrada: {interface.__name__}")
        return self
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve um serviço e suas dependências.
        
        Args:
            service_type: Tipo do serviço a ser resolvido
            
        Returns:
            Instância do serviço
            
        Raises:
            ValueError: Se o serviço não estiver registrado
            TypeError: Se houver problemas na resolução de dependências
        """
        # Verifica se já existe como singleton
        if service_type in self._singletons:
            return self._singletons[service_type]
        
        # Verifica se é factory
        if service_type in self._factories:
            instance = self._factories[service_type]()
            
            # Armazena como singleton se não for transient
            if service_type not in self._transient_types:
                self._singletons[service_type] = instance
            
            return instance
        
        # Verifica se é classe registrada
        if service_type in self._services:
            implementation = self._services[service_type]
            
            if not inspect.isclass(implementation):
                # É uma instância já criada
                return implementation
            
            # Cria instância com resolução de dependências
            instance = self._create_instance(implementation)
            
            # Armazena como singleton se não for transient
            if service_type not in self._transient_types:
                self._singletons[service_type] = instance
            
            return instance
        
        # Tenta resolver automaticamente se for uma classe concreta
        if inspect.isclass(service_type):
            instance = self._create_instance(service_type)
            
            # Não armazena automaticamente - apenas para classes explicitamente registradas
            return instance
        
        raise ValueError(f"Serviço não registrado: {service_type}")
    
    def _create_instance(self, cls: Type[T]) -> T:
        """
        Cria instância de uma classe resolvendo suas dependências.
        
        Args:
            cls: Classe a ser instanciada
            
        Returns:
            Instância da classe
        """
        try:
            # Obtém o construtor
            constructor = cls.__init__
            
            # Obtém type hints dos parâmetros
            type_hints = get_type_hints(constructor)
            
            # Obtém assinatura do construtor
            sig = inspect.signature(constructor)
            
            # Resolve parâmetros
            kwargs = {}
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                # Obtém o tipo do parâmetro
                param_type = type_hints.get(param_name, param.annotation)
                
                if param_type == inspect.Parameter.empty:
                    # Sem type hint - pula se tem valor padrão
                    if param.default != inspect.Parameter.empty:
                        continue
                    else:
                        raise TypeError(f"Parâmetro {param_name} em {cls.__name__} precisa de type hint")
                
                # Resolve a dependência
                try:
                    dependency = self.resolve(param_type)
                    kwargs[param_name] = dependency
                except ValueError:
                    # Se não conseguir resolver e tem valor padrão, usa o padrão
                    if param.default != inspect.Parameter.empty:
                        continue
                    else:
                        raise ValueError(f"Não foi possível resolver dependência {param_type} para {cls.__name__}.{param_name}")
            
            # Cria a instância
            instance = cls(**kwargs)
            logging.debug(f"Instância criada: {cls.__name__} com dependências: {list(kwargs.keys())}")
            return instance
            
        except Exception as e:
            logging.error(f"Erro ao criar instância de {cls.__name__}: {e}")
            raise
    
    def clear(self) -> None:
        """Limpa todos os serviços registrados."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._transient_types.clear()
        logging.debug("Container DI limpo")
    
    def is_registered(self, service_type: Type) -> bool:
        """Verifica se um serviço está registrado."""
        return (service_type in self._services or 
                service_type in self._factories or 
                service_type in self._singletons)
    
    def get_registered_services(self) -> Dict[Type, str]:
        """Retorna lista de serviços registrados para debug."""
        services = {}
        
        for service_type in self._services:
            impl = self._services[service_type]
            impl_name = impl.__name__ if inspect.isclass(impl) else str(impl)
            services[service_type] = f"Class: {impl_name}"
        
        for service_type in self._factories:
            factory = self._factories[service_type]
            services[service_type] = f"Factory: {factory.__name__}"
        
        for service_type in self._singletons:
            instance = self._singletons[service_type]
            services[service_type] = f"Singleton: {type(instance).__name__}"
        
        return services


# Instância global do container
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """Obtém a instância global do container DI."""
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def inject(func: Callable) -> Callable:
    """
    Decorator que injeta dependências automaticamente em uma função.
    
    As dependências são resolvidas baseadas nos type hints dos parâmetros.
    
    Example:
        >>> @inject
        ... def process_user(user_repo: IUserRepository, logger: ILogger):
        ...     logger.info("Processing user...")
        ...     return user_repo.get_all()
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        container = get_container()
        
        # Obtém type hints
        type_hints = get_type_hints(func)
        
        # Obtém assinatura
        sig = inspect.signature(func)
        
        # Resolve parâmetros não fornecidos
        for param_name, param in sig.parameters.items():
            if param_name in kwargs:
                continue  # Já fornecido
            
            param_type = type_hints.get(param_name, param.annotation)
            
            if param_type == inspect.Parameter.empty:
                continue  # Sem type hint
            
            try:
                dependency = container.resolve(param_type)
                kwargs[param_name] = dependency
            except ValueError:
                # Se não conseguir resolver e tem valor padrão, deixa usar o padrão
                if param.default == inspect.Parameter.empty:
                    raise ValueError(f"Não foi possível resolver dependência {param_type} para {func.__name__}.{param_name}")
        
        return func(*args, **kwargs)
    
    return wrapper


def injectable(cls: Type[T]) -> Type[T]:
    """
    Decorator que marca uma classe como injetável.
    
    Automaticamente registra a classe no container como singleton.
    
    Example:
        >>> @injectable
        ... class UserService:
        ...     def __init__(self, user_repo: IUserRepository):
        ...         self.user_repo = user_repo
    """
    container = get_container()
    container.register_singleton(cls, cls)
    return cls


def service(interface: Type, singleton: bool = True):
    """
    Decorator que registra uma classe como implementação de uma interface.
    
    Args:
        interface: Interface/tipo abstrato
        singleton: Se deve ser singleton
        
    Example:
        >>> @service(IUserRepository)
        ... class SqlUserRepository:
        ...     pass
    """
    def decorator(cls: Type):
        container = get_container()
        container.register(interface, cls, singleton=singleton)
        return cls
    
    return decorator


# Exemplo de uso e configuração
def setup_dependencies():
    """Configura as dependências da aplicação."""
    container = get_container()
    
    # Exemplo de configuração - deve ser adaptado para WATS
    logging.info("Configurando dependências da aplicação...")
    
    # Registrar serviços reais aqui
    # container.register_singleton(ILogger, FileLogger)
    # container.register_singleton(IUserRepository, SqlUserRepository)
    # etc.
    
    logging.info("Dependências configuradas com sucesso")