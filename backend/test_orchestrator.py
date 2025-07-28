# test_orchestrator.py
print("=== Testing Orchestrator ===")

try:
    print("1. Testing orchestrator import...")
    from agents.orchestrator import OrchestratorAgent
    print('✅ Orchestrator import successful')
    
    print("2. Testing orchestrator initialization...")
    orchestrator = OrchestratorAgent()
    print('✅ Orchestrator initialized successfully')
    
    print("3. Testing database manager...")
    if hasattr(orchestrator, 'db_manager'):
        properties = orchestrator.db_manager.search_properties({})
        print(f'✅ Database has {len(properties)} properties')
    else:
        print('❌ No db_manager found in orchestrator')
    
    print("4. Testing orchestrator query handling...")
    test_query = 'Find 2BHK apartments'
    response = orchestrator.handle_query(test_query)
    print(f'✅ Query handled successfully')
    print(f'Response: {response}')
    
    print("=== All tests passed! ===")
    
except ImportError as import_error:
    print(f'❌ Import Error: {import_error}')
    print("This means there's an issue with your agent files or imports")
    import traceback
    traceback.print_exc()
    
except Exception as e:
    print(f'❌ Error: {e}')
    print("This tells us exactly what's failing in your orchestrator")
    import traceback
    traceback.print_exc()
