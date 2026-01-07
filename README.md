# A Voting-based Blockchain Interoperability Oracle

Prototypical implementation of the smart contracts and oracle node for a voting-based blockchain interoperability oracle. The oracle allows clients to verify that a transaction is included in another blockchain but is currently limited to Ethereum-based blockchains.

## Prerequisites

You need to have the following software installed:

* [Golang](https://golang.org/doc/install) (version 1.15)
* [Node.js](https://nodejs.org/) (version >= 15.4.0)
* [Truffle](https://www.trufflesuite.com/truffle) (version 5.3.7)
* [Ganache](https://www.trufflesuite.com/ganache) (version >= 2.5.4)
* [Solidity](https://docs.soliditylang.org/en/latest/installing-solidity.html) (^0.8.0)

## Installation

### Smart Contract Deployment

1. Change into the contract directory: `cd ioporaclecontracts/`
2. Install all dependencies: `npm install`
3. Deploy contracts: `truffle migrate --reset`

### Building the Oracle Node

1. Change into the node directory: `cd ioporaclenode/`
2. Build the node: `go build -o ioporaclenode ./cmd/ioporaclenode/`

## Configuration

The oracle node uses a configuration file which should be specified through the respective command-line flag. To see what the config file should look like, one can take a look at the example configuration file which resides in the `configs` directory.

## Cost Analysis

The project includes two alternative implementations of oracle contracts. One implements an on-chain aggregation mechanism whereas each oracle node calls the oracle contract to submit a result. The second oracle contract makes use of ECDSA signatures to verify the result. To repeat the experiments one can use the provided evaluation scripts. The results are then saved in a CSV file in `./ioporaclecontracts/data`.

### BLS

1. Run a local Ethereum blockchain (Ganache).
2. Deploy the smart contracts on the local blockchain with `truffle migrate --reset`.
3. Run your own [IOTA node](https://github.com/gohornet/hornet) (or use a public node with MQTT enabled).
4. Create the configuration files for three oracle nodes.
5. Start the oracle nodes which are able to answer to the requests.

    * Run `./ioporacle -c ./configs/config_n1.json`
    * Run `./ioporacle -c ./configs/config_n2.json`
    * Run `./ioporacle -c ./configs/config_n3.json`

6. Run `truffle execute ./scripts/eval/eval-bls-cost.js`

### ECDSA

1. Run a local Ethereum blockchain (Ganache).
2. Change into the contract directory: `cd ioporaclecontracts/`
3. Run `truffle execute ./scripts/eval/eval-ecdsa-cost.js`

### On-Chain

1. Run a local Ethereum blockchain (Ganache).
2. Change into the contract directory: `cd ioporaclecontracts/`
3. Run `truffle execute ./scripts/eval/eval-on-chain-cost.js`

## Contributing

This is a research prototype. We welcome anyone to contribute. File a bug report or submit feature requests through the issue tracker. If you want to contribute feel free to submit a pull request.

## Acknowledgement

The financial support by the Austrian Federal Ministry for Digital and Economic Affairs, the National Foundation for Research, Technology and Development as well as the Christian Doppler Research Association is gratefully acknowledged.

This project is licensed under the [MIT License](LICENSE).

启动本地区块链 (Ganache)。
 运行管理控制台：
    ```bash
    python gui.py
    ```
 操作流程:
     *步骤 1:** 点击 **部署智能合约 (Deploy)**。
     *步骤 2:** 点击 **编译 Go 节点 (Build)**。
     *步骤 3:** 选择节点数量并点击 **配置 Ganache 私钥**。
     *步骤 4:** 点击 **一键启动所有节点 (Start)**。
     *步骤 5:** 选择一个文件进行签名。
     *步骤 6:** 点击 **启动签名 & 聚合 (Trigger)**。在大屏中观察实时生成的聚合签名 $(S, R)$。
     *步骤 7:** 点击 **上链存证 & 验证 (Submit)** 以完成链上确认。

 📄 许可证 (License)

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。
