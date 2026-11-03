"""The documented evaluation commands work without a hidden PYTHONPATH setting."""
import os
import subprocess
import sys
from pathlib import Path
import pytest

@pytest.mark.parametrize('script',['check_model_acceptance.py','check_policy_model.py','check_advice_model.py','publish_acceptance_evidence.py'])
def test_evaluation_help_outside_repository_without_pythonpath(tmp_path,script):
    root=Path(__file__).resolve().parents[1]
    env=dict(os.environ);env.pop('PYTHONPATH',None)
    result=subprocess.run([sys.executable,str(root/'scripts'/script),'--help'],cwd=tmp_path,env=env,capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr
    assert 'usage:' in result.stdout
