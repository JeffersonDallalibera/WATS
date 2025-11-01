"""
Script de Teste e Benchmark das Otimizações de Performance
Valida e mede o ganho de performance do Connection Pool e Cache
"""

import time
import logging
from typing import List, Dict, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)


def test_connection_pool():
    """Testa Connection Pool comparando com conexões diretas."""
    print("\n" + "="*60)
    print("🔌 TESTE 1: CONNECTION POOL vs CONEXÕES DIRETAS")
    print("="*60)
    
    from src.wats.config import Settings
    from src.wats.db.connection_pool import get_connection_pool, close_connection_pool
    import pyodbc
    
    # Carrega config
    settings = Settings()
    
    # Monta connection string
    driver = settings.get_database_setting("driver", "ODBC Driver 17 for SQL Server")
    server = settings.get_database_setting("server")
    database = settings.get_database_setting("database")
    uid = settings.get_database_setting("uid")
    pwd = settings.get_database_setting("pwd")
    
    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={uid};"
        f"PWD={pwd};"
        "TrustServerCertificate=yes;"
    )
    
    num_queries = 50
    
    # Teste 1: Conexões diretas (método antigo)
    print(f"\n📊 Executando {num_queries} queries COM conexões diretas...")
    start_direct = time.time()
    
    for i in range(num_queries):
        conn = pyodbc.connect(conn_str, timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
    
    time_direct = time.time() - start_direct
    print(f"✓ Tempo: {time_direct:.3f}s")
    print(f"  Média por query: {time_direct/num_queries*1000:.1f}ms")
    
    # Teste 2: Connection Pool (método novo)
    print(f"\n📊 Executando {num_queries} queries COM Connection Pool...")
    pool = get_connection_pool(conn_str, pool_size=5, max_overflow=10)
    
    start_pool = time.time()
    
    for i in range(num_queries):
        with pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
    
    time_pool = time.time() - start_pool
    print(f"✓ Tempo: {time_pool:.3f}s")
    print(f"  Média por query: {time_pool/num_queries*1000:.1f}ms")
    
    # Resultados
    improvement = ((time_direct - time_pool) / time_direct) * 100
    speedup = time_direct / time_pool
    
    print(f"\n{'='*60}")
    print(f"🎯 RESULTADO:")
    print(f"   Melhoria: {improvement:.1f}%")
    print(f"   Speedup: {speedup:.2f}x mais rápido")
    print(f"   Tempo economizado: {time_direct - time_pool:.3f}s")
    print(f"{'='*60}")
    
    close_connection_pool()
    
    return improvement


def test_cache_system():
    """Testa sistema de cache."""
    print("\n" + "="*60)
    print("💾 TESTE 2: SISTEMA DE CACHE")
    print("="*60)
    
    from src.wats.utils.cache import get_cache, cached
    
    cache = get_cache(default_ttl=300)
    
    # Função simulada que "busca" dados do banco
    query_count = [0]  # Counter mutável
    
    @cached(ttl=60, key_prefix="test")
    def expensive_query(param):
        """Simula uma query cara ao banco."""
        query_count[0] += 1
        time.sleep(0.1)  # Simula latência do banco
        return f"result_for_{param}"
    
    num_requests = 100
    num_unique_params = 10
    
    print(f"\n📊 Executando {num_requests} requests (com {num_unique_params} parâmetros únicos)...")
    
    start = time.time()
    
    for i in range(num_requests):
        param = i % num_unique_params  # Gera apenas 10 parâmetros únicos
        result = expensive_query(param)
    
    elapsed = time.time() - start
    
    stats = cache.get_stats()
    
    print(f"✓ Tempo total: {elapsed:.3f}s")
    print(f"  Queries executadas: {query_count[0]}")
    print(f"  Cache hits: {stats['hits']}")
    print(f"  Cache misses: {stats['misses']}")
    print(f"  Hit rate: {stats['hit_rate']:.1f}%")
    
    # Calcular tempo sem cache
    time_without_cache = num_requests * 0.1
    improvement = ((time_without_cache - elapsed) / time_without_cache) * 100
    
    print(f"\n{'='*60}")
    print(f"🎯 RESULTADO:")
    print(f"   Tempo sem cache: {time_without_cache:.3f}s")
    print(f"   Tempo com cache: {elapsed:.3f}s")
    print(f"   Melhoria: {improvement:.1f}%")
    print(f"   Redução de queries: {100 - (query_count[0]/num_requests*100):.1f}%")
    print(f"{'='*60}")
    
    cache.clear()
    
    return improvement


def test_combined_performance():
    """Testa performance combinada em cenário real."""
    print("\n" + "="*60)
    print("🚀 TESTE 3: PERFORMANCE COMBINADA (CENÁRIO REAL)")
    print("="*60)
    
    from src.wats.config import Settings
    from src.wats.db.database_manager import DatabaseManager
    from src.wats.db.connection_pool import get_connection_pool
    from src.wats.utils.cache import get_cache, cached
    
    settings = Settings()
    
    # Inicializa connection pool
    driver = settings.get_database_setting("driver", "ODBC Driver 17 for SQL Server")
    server = settings.get_database_setting("server")
    database = settings.get_database_setting("database")
    uid = settings.get_database_setting("uid")
    pwd = settings.get_database_setting("pwd")
    
    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={uid};"
        f"PWD={pwd};"
        "TrustServerCertificate=yes;"
    )
    
    pool = get_connection_pool(conn_str, pool_size=5, max_overflow=10)
    cache = get_cache(default_ttl=300)
    
    print("\n📊 Simulando 100 requisições de usuário...")
    print("  - 50% são queries repetidas (benefício do cache)")
    print("  - 50% são queries únicas")
    
    @cached(ttl=60, key_prefix="user")
    def get_user_connections(user_id):
        """Simula busca de conexões do usuário."""
        with pool.get_connection() as conn:
            cursor = conn.cursor()
            # Query simples para teste
            cursor.execute("SELECT TOP 10 * FROM Conexao_WTS")
            return cursor.fetchall()
    
    num_requests = 100
    unique_users = 20
    
    start = time.time()
    
    for i in range(num_requests):
        user_id = i % unique_users  # Simula 20 usuários diferentes
        try:
            connections = get_user_connections(user_id)
        except Exception as e:
            print(f"⚠️  Erro na query {i}: {e}")
    
    elapsed = time.time() - start
    
    stats = cache.get_stats()
    avg_per_request = elapsed / num_requests * 1000
    
    print(f"\n✓ Tempo total: {elapsed:.3f}s")
    print(f"  Média por request: {avg_per_request:.1f}ms")
    print(f"  Cache hit rate: {stats['hit_rate']:.1f}%")
    print(f"  Throughput: {num_requests/elapsed:.1f} req/s")
    
    print(f"\n{'='*60}")
    print(f"🎯 ANÁLISE:")
    
    if avg_per_request < 50:
        print("   🟢 EXCELENTE: Menos de 50ms por request")
    elif avg_per_request < 100:
        print("   🟡 BOM: Entre 50-100ms por request")
    else:
        print("   🔴 ATENÇÃO: Mais de 100ms por request")
    
    if stats['hit_rate'] > 70:
        print(f"   🟢 CACHE EFICIENTE: {stats['hit_rate']:.1f}% hit rate")
    else:
        print(f"   🟡 CACHE PODE MELHORAR: {stats['hit_rate']:.1f}% hit rate")
    
    print(f"{'='*60}")


def run_all_tests():
    """Executa todos os testes de benchmark."""
    print("\n")
    print("=" * 80)
    print(" " * 20 + "🚀 WATS PERFORMANCE BENCHMARK")
    print("=" * 80)
    
    improvements = []
    
    try:
        # Teste 1: Connection Pool
        improvement1 = test_connection_pool()
        improvements.append(("Connection Pool", improvement1))
    except Exception as e:
        print(f"❌ Erro no teste de Connection Pool: {e}")
    
    try:
        # Teste 2: Cache System
        improvement2 = test_cache_system()
        improvements.append(("Cache System", improvement2))
    except Exception as e:
        print(f"❌ Erro no teste de Cache: {e}")
    
    try:
        # Teste 3: Performance combinada
        test_combined_performance()
    except Exception as e:
        print(f"❌ Erro no teste combinado: {e}")
    
    # Resumo final
    print("\n" + "=" * 80)
    print(" " * 30 + "📊 RESUMO FINAL")
    print("=" * 80)
    
    if improvements:
        print("\n🎯 Melhorias Medidas:")
        total_improvement = 0
        for name, improvement in improvements:
            print(f"   • {name}: {improvement:.1f}% de melhoria")
            total_improvement += improvement
        
        avg_improvement = total_improvement / len(improvements)
        print(f"\n   ✅ Melhoria Média: {avg_improvement:.1f}%")
        
        if avg_improvement > 50:
            print("\n   🏆 RESULTADO EXCELENTE! Performance significativamente melhorada!")
        elif avg_improvement > 30:
            print("\n   ✅ RESULTADO POSITIVO! Boa melhoria de performance!")
        else:
            print("\n   ℹ️  Melhoria moderada, considere otimizações adicionais")
    
    print("\n" + "=" * 80)
    print(" " * 25 + "✅ BENCHMARK CONCLUÍDO")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_all_tests()
