# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None
platform = sys.platform

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('ui/static', 'ui/static'),
        ('ui/index.html', 'ui'),
        ('ui/main.py', 'ui'),
        ('ui_story', 'ui_story'),
        ('agent_dir', 'agent_dir'),
        ('tools', 'tools')
    ],
    hiddenimports=['aiohappyeyeballs', 'aiohttp', 'aiosignal', 'aiosqlite', 'annotated_doc', 'annotated_types', 'anyio', 'attrs', 'bottle', 'certifi', 'cffi', 'charset_normalizer', 'click', 'cryptography', 'distro', 'fastapi', 'fastembed', 'filelock', 'filetype', 'firecrawl_py', 'flatbuffers', 'frozenlist', 'fsspec', 'google_auth', 'google_genai', 'greenlet', 'grpcio', 'h11', 'h2', 'hf_xet', 'hpack', 'httpcore', 'httpcore2', 'httpx', 'httpx_sse', 'httpx2', 'huggingface_hub', 'hyperframe', 'idna', 'jiter', 'jsonpatch', 'jsonpointer', 'jsonschema', 'jsonschema_specifications', 'langchain', 'langchain_core', 'langchain_google_genai', 'langchain_mcp_adapters', 'langchain_openai', 'langchain_protocol', 'langgraph', 'langgraph_checkpoint', 'langgraph_checkpoint_sqlite', 'langgraph_prebuilt', 'langgraph_sdk', 'langsmith', 'loguru', 'mcp', 'mmh3', 'multidict', 'nest_asyncio', 'numpy', 'onnxruntime', 'openai', 'orjson', 'ormsgpack', 'packaging', 'pillow', 'playwright', 'portalocker', 'propcache', 'protobuf', 'proxy_tools', 'psutil', 'py_rust_stemmers', 'pyasn1', 'pyasn1_modules', 'pycparser', 'pydantic', 'pydantic_settings', 'pydantic_core', 'pyee', 'PyJWT', 'PyQt5', 'PyQt5_Qt5', 'PyQt5_sip', 'PyQtWebEngine', 'PyQtWebEngine_Qt5', 'python_dotenv', 'python_multipart', 'pywebview', 'PyYAML', 'qdrant_client', 'QtPy', 'referencing', 'regex', 'requests', 'requests_toolbelt', 'rpds_py', 'sniffio', 'sqlcipher3_binary', 'sqlite_vec', 'sse_starlette', 'starlette', 'tenacity', 'tiktoken', 'tokenizers', 'tqdm', 'truststore', 'typing_inspection', 'typing_extensions', 'urllib3', 'uuid_utils', 'uvicorn', 'websockets', 'xxhash', 'yarl', 'zstandard', 'sqlcipher3'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['proxy_server', 'ui/old'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if platform == 'win32':
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='SwaraAI',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
else:
    # Linux / Kali
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='swara-ai',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
