# ShipReceipt

ShipReceipt 是一个本地优先的命令行工具，用来为文件交付目录创建和验证防篡改交付凭证。它会记录每个文件的相对路径、大小和 SHA-256 摘要，并生成确定性的 JSON receipt，后续可以验证目录是否被修改。

ShipReceipt 没有运行时依赖。可选的 HMAC-SHA256 签名可以证明凭证由持有本地共享签名密钥的一方创建。

## 运行示例

```console
$ shipreceipt keygen signing.key
KEY CREATED signing.key

$ shipreceipt create ./release-bundle --output release.receipt.json --key signing.key --label v0.1.0
CREATED release.receipt.json files=2 id=sha256:... auth=signed

$ shipreceipt verify release.receipt.json --root ./release-bundle --key signing.key
VERIFIED sha256:...
```

文件被修改时，验证会返回非零退出码：

```console
$ shipreceipt verify release.receipt.json --root ./release-bundle --key signing.key
FAILED
changed: app.bin
```

## 为什么需要它

小团队经常通过对象存储、网盘或制品系统传递构建产物、数据集、报告和发布包。普通 checksum 文件能证明单个文件内容，但很难同时保留路径、大小、排除规则、创建元数据和可选认证。ShipReceipt 把这些信息放进一个可审计、可复现的 JSON 凭证中。

## 功能列表

- 递归扫描目录，并以流式 SHA-256 计算文件摘要。
- 记录相对 POSIX 路径、文件大小和内容摘要。
- 生成确定性的规范化 receipt 摘要，适合复现构建。
- 检测文件修改、缺失和新增。
- 支持可选 HMAC-SHA256 凭证认证。
- 拒绝不安全的 receipt 路径和本地符号链接。
- 原子写入 receipt 文件。
- 提供 `create`、`verify`、`inspect`、`keygen` 命令。

## 安装

从 clone 后的目录安装：

```console
python -m pip install .
```

开发安装：

```console
python -m pip install -e ".[dev]"
```

构建独立 Python zipapp：

```console
python scripts/build_zipapp.py
python dist/shipreceipt.pyz --version
```

## 快速开始

```console
mkdir release-bundle
echo "payload" > release-bundle/artifact.txt
shipreceipt create release-bundle --output release.receipt.json --label first-drop
shipreceipt verify release.receipt.json --root release-bundle
```

签名凭证流程：

```console
shipreceipt keygen signing.key
shipreceipt create release-bundle --output release.receipt.json --key signing.key
shipreceipt verify release.receipt.json --root release-bundle --key signing.key
```

## 使用示例

```console
shipreceipt keygen PATH
shipreceipt create ROOT --output RECEIPT [--key KEY] [--label LABEL] [--exclude PATTERN]
shipreceipt verify RECEIPT --root ROOT [--key KEY] [--require-signature]
shipreceipt inspect RECEIPT [--json]
```

`--exclude` 使用 shell 风格模式，例如 `*.log`，可以重复传入。ShipReceipt 默认排除 `.git`、`__pycache__` 和 Python 字节码文件。

## 配置说明

ShipReceipt 通过命令行参数配置。它不读取全局配置文件、环境变量或网络服务。

签名密钥由 `shipreceipt keygen` 创建。建议把密钥放在交付目录之外。如果密钥或输出 receipt 位于被扫描目录内，CLI 会在当前命令中排除该路径。

## 架构说明

包被拆成几个小模块：

- `inventory`：文件遍历、排除规则和流式哈希。
- `service`：凭证创建、manifest 摘要、签名和验证。
- `keys`：本地签名密钥生成和读取。
- `io`：receipt JSON 读取和原子写入。
- `cli`：命令行参数和退出码。

详见 [docs/architecture.md](docs/architecture.md) 和 [docs/receipt-format.md](docs/receipt-format.md)。

## 性能说明

文件内容按 1 MiB 分块计算哈希，所以内存占用不会随着最大文件大小线性增长。receipt 本身会保存在内存中，因为它通常远小于被交付的文件。

## 安全说明

ShipReceipt 是完整性和真实性工具，不是加密工具。它不会隐藏 receipt 中的文件名、大小或元数据。HMAC 签名只能证明凭证由持有共享本地密钥的一方创建。

安全策略见 [SECURITY.md](SECURITY.md)。

## Roadmap

- v0.1.x：稳定 receipt schema 和 CLI 输出。
- v0.2.x：增加机器可读的验证报告。
- v0.3.x：增加可选公钥签名支持。
- v0.4.x：增加可复现发布包辅助工具。

## Contributing

欢迎通过 issue 和 pull request 参与。请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## License

ShipReceipt 使用 MIT License 发布。见 [LICENSE](LICENSE)。
