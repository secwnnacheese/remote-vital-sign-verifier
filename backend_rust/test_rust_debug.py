import sys, os
print('START')
print('cwd:', os.getcwd())
print('PYTHONPATH includes parent?')
print('\n'.join(sys.path[:3]))
try:
    from rust_bridge import RustBridge
    print('imported rust_bridge')
    rb = RustBridge()
    res = rb.run_job({'mode':'add','f1':1.0,'a1':1.0,'p1':0.0,'f2':2.0,'a2':0.5,'p2':0.0,'duration':0.1,'dt':0.01})
    print('res meta:', res.get('meta'))
    print('time len:', len(res.get('time',[])))
except Exception as e:
    import traceback
    traceback.print_exc()
    print('EXCEPTION:', e)
