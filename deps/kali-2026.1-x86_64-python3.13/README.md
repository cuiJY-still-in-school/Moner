# 依赖包目录
平台: kali-2026.1-x86_64-python3.13
打包时间: 2026年 04月 06日 星期一 09:11:54 CST

## 包含的包
57 个包

## 使用方法
1. 确保在项目根目录
2. 运行安装脚本:
   ```bash
   cd deps/kali-2026.1-x86_64-python3.13
   ./install-deps.sh
   ```

或使用pip直接安装:
```bash
pip install --no-index --find-links deps/kali-2026.1-x86_64-python3.13 -r requirements.txt
```

## 注意事项
- 这些包是针对特定平台和Python版本编译的
- 如果平台或Python版本不匹配，可能需要重新打包
- 对于Python 3.13，pydantic-core可能需要特殊处理
