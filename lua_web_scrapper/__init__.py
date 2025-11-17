# Patch para corrigir problema com jwt.PyJWTError no django-allauth
# Deve ser importado antes de qualquer importação do allauth
# Este patch garante que o PyJWT seja importado corretamente mesmo se houver
# namespace packages conflitantes no sys.path
import sys

# Força a importação do PyJWT antes de qualquer outra coisa
try:
    # Remove qualquer módulo jwt já importado (namespace package vazio)
    if 'jwt' in sys.modules:
        jwt_module = sys.modules['jwt']
        # Se for um namespace package vazio, remove para forçar reimportação
        if not hasattr(jwt_module, 'decode') and not hasattr(jwt_module, 'PyJWTError'):
            del sys.modules['jwt']
    
    # Importa o PyJWT corretamente
    import jwt
    from jwt import exceptions as jwt_exceptions
    
    # Garante que PyJWTError esteja disponível diretamente no módulo jwt
    # Isso corrige um bug conhecido onde PyJWTError pode não estar acessível
    if not hasattr(jwt, 'PyJWTError'):
        jwt.PyJWTError = jwt_exceptions.PyJWTError
    
    # Garante que todas as exceções do jwt estejam acessíveis no módulo principal
    for attr_name in dir(jwt_exceptions):
        if not attr_name.startswith('_') and not hasattr(jwt, attr_name):
            setattr(jwt, attr_name, getattr(jwt_exceptions, attr_name))
    
    # Garante que decode esteja disponível
    if not hasattr(jwt, 'decode'):
        try:
            jwt.decode = jwt.api_jwt.decode
        except AttributeError:
            # Tenta importar diretamente da API
            from jwt.api_jwt import decode as jwt_decode
            jwt.decode = jwt_decode
except (ImportError, AttributeError) as e:
    # Se houver erro, tenta uma abordagem alternativa
    try:
        # Força importação direta do PyJWT
        import importlib.util
        jwt_spec = importlib.util.find_spec('jwt')
        if jwt_spec and jwt_spec.origin:
            jwt_module = importlib.util.module_from_spec(jwt_spec)
            jwt_spec.loader.exec_module(jwt_module)
            sys.modules['jwt'] = jwt_module
    except Exception:
        pass  # jwt não está instalado ou há problema na importação, ignora
