import customtkinter as ctk
import subprocess
import threading
import os
import json
import re
import time
from tkinter import filedialog, messagebox

# ================= 配置区域 =================
BASE_DIR = "/home/st/下载/research-ioporacle-main"
CONTRACTS_DIR = os.path.join(BASE_DIR, "ioporaclecontracts")
NODE_DIR = os.path.join(BASE_DIR, "ioporaclenode")
CONFIG_DIR = os.path.join(NODE_DIR, "configs")
SCRIPTS_DIR = os.path.join(CONTRACTS_DIR, "scripts")
BUILD_DIR = os.path.join(CONTRACTS_DIR, "build/contracts") 

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SystemGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("基于 BN256 聚合签名的分布式多链预言机系统 ")
        self.geometry("1450x950")

        self.log_font = self.detect_system_font(size=13)
        self.ui_font = self.detect_system_font(size=14, weight="bold")
        self.node_processes = {}     
        self.deployment_output = ""  
        self.selected_file_path = "" 
        
        self.final_hash = ""
        self.captured_s = ""
        self.captured_r = ""
        
        self.log_widgets = {} 

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ============ 左侧侧边栏 ============
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(16, weight=1)

        ctk.CTkLabel(self.sidebar_frame, text="系统控制面板", font=ctk.CTkFont(family=self.ui_font._family, size=22, weight="bold")).grid(row=0, column=0, padx=20, pady=(30, 20))

        self.create_sidebar_button("1. 部署智能合约 (Deploy)", self.deploy_contracts, row=1)
        self.create_sidebar_button("2. 编译 Go 节点 (Build)", self.compile_node, row=2)
        
        ctk.CTkLabel(self.sidebar_frame, text="3. 选择节点数量:", font=self.ui_font, anchor="w").grid(row=3, column=0, padx=20, pady=(10, 0))
        self.node_count_var = ctk.StringVar(value="5")
        self.slider_nodes = ctk.CTkSegmentedButton(self.sidebar_frame, values=["1", "2", "3", "4", "5"], variable=self.node_count_var, font=self.ui_font)
        self.slider_nodes.grid(row=4, column=0, padx=20, pady=5)

        self.create_sidebar_button("4. 一键回填地址 (静默修复)", self.auto_fill_addresses, row=5, color="#2CC985", hover="#229A65")
        self.create_sidebar_button("6. 配置 Ganache 私钥 (Wallet)", self.open_key_config_window, row=6)
        
        self.btn_kill = ctk.CTkButton(self.sidebar_frame, text="⚠ 强制清理旧进程", font=self.ui_font, fg_color="gray", hover_color="#555", height=30, command=self.kill_all_nodes)
        self.btn_kill.grid(row=7, column=0, padx=20, pady=10)

        self.create_sidebar_button("7. 一键启动所有节点 (Start)", self.start_nodes, row=8, color="#D35B58", hover="#C72C41", height=50)

        ctk.CTkFrame(self.sidebar_frame, height=2, fg_color="#555").grid(row=9, column=0, sticky="ew", padx=20, pady=15)

        ctk.CTkLabel(self.sidebar_frame, text="签名任务:", font=self.ui_font, anchor="w").grid(row=10, column=0, padx=20, pady=(5,0))
        self.btn_file = ctk.CTkButton(self.sidebar_frame, text="8. 选择文件", font=self.ui_font, command=self.select_file)
        self.btn_file.grid(row=11, column=0, padx=20, pady=10)
        self.lbl_file = ctk.CTkLabel(self.sidebar_frame, text="未选择文件", font=self.log_font, text_color="gray", wraplength=200)
        self.lbl_file.grid(row=12, column=0, padx=20, pady=0)

        self.create_sidebar_button("9. 启动签名 & 聚合 (Trigger)", self.start_signing, row=13, color="#3B8ED0", hover="#36719F", height=50)
        self.create_sidebar_button("10. 上链存证 & 验证 (Submit)", self.start_proof_submission, row=14, color="#9B59B6", hover="#8E44AD", height=50)

        # ============ 右侧主要区域 ============
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.right_frame.grid_rowconfigure(1, weight=3) 
        self.right_frame.grid_rowconfigure(3, weight=1) 
        self.right_frame.grid_columnconfigure(0, weight=1)

        # --- 1. 日志区 ---
        self.log_tabview = ctk.CTkTabview(self.right_frame)
        self.log_tabview.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        self.tabs = ["系统日志"] + [f"节点 {i}" for i in range(1, 6)]
        for t in self.tabs:
            self.log_tabview.add(t)
            textbox = ctk.CTkTextbox(self.log_tabview.tab(t), font=self.log_font, wrap="none")
            textbox.pack(expand=True, fill="both", padx=5, pady=5)
            textbox.configure(state="disabled")
            
            textbox.tag_config("info", foreground="#DDDDDD")
            textbox.tag_config("error", foreground="#FF5555")
            textbox.tag_config("success", foreground="#55FF55")
            textbox.tag_config("sign", foreground="#00FFFF")
            
            self.log_widgets[t] = textbox

        # --- 2. 签名结果可视化区 (大屏) ---
        self.result_frame = ctk.CTkFrame(self.right_frame, fg_color="#101010", corner_radius=10, border_width=2, border_color="#555")
        self.result_frame.grid(row=3, column=0, sticky="nsew", pady=(15, 0))
        self.result_frame.grid_columnconfigure(0, weight=1)
        self.result_frame.grid_rowconfigure(1, weight=1)

        result_label = ctk.CTkLabel(self.result_frame, text="📊 分布式签名实时监控大屏 (Live Signature Monitor)", font=ctk.CTkFont(family=self.ui_font._family, size=16, weight="bold"), text_color="#eee")
        result_label.grid(row=0, column=0, sticky="w", padx=15, pady=5)

        self.result_box = ctk.CTkTextbox(self.result_frame, font=ctk.CTkFont(family=self.ui_font._family, size=14, weight="bold"), height=250, fg_color="#000")
        self.result_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.result_box.tag_config("header_node", foreground="#00FFFF") 
        self.result_box.tag_config("header_total", foreground="#00FF00") 
        self.result_box.tag_config("step", foreground="#FFA500")        
        self.result_box.tag_config("data", foreground="#FFFFFF")        
        self.result_box.tag_config("trigger", foreground="#FF00FF")     
        self.result_box.tag_config("final_success", foreground="#00FF00")
        
        self.result_box.insert("end", ">>> 系统就绪，等待签名任务...\n", "data")
        self.result_box.configure(state="disabled")

    # ============ 辅助函数 ============
    
    def detect_system_font(self, size=12, weight="normal"):
        font_candidates = ["WenQuanYi Micro Hei", "Noto Sans CJK SC", "Droid Sans Fallback", "SimHei", "Microsoft YaHei", "Sans"]
        selected_font = "Sans"
        try:
            result = subprocess.run(['fc-list', ':family'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                for f in font_candidates:
                    if f in result.stdout:
                        selected_font = f
                        break
        except: pass
        return ctk.CTkFont(family=selected_font, size=size, weight=weight)

    def create_sidebar_button(self, text, command, row, color=None, hover=None, height=40):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, font=self.ui_font, command=command, height=height)
        if color: btn.configure(fg_color=color)
        if hover: btn.configure(hover_color=hover)
        btn.grid(row=row, column=0, padx=20, pady=8)
        return btn

    def log(self, tab_name, message, tag="info"):
        if tab_name == "System": tab_name = "系统日志"
        elif "Node" in tab_name: tab_name = tab_name.replace("Node", "节点")
        
        target_widget = self.log_widgets.get(tab_name, self.log_widgets["系统日志"])
        target_widget.configure(state="normal")
        target_widget.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n", tag)
        target_widget.see("end")
        target_widget.configure(state="disabled")
        if tab_name != "系统日志" and tag == "error":
            sys_widget = self.log_widgets["系统日志"]
            sys_widget.configure(state="normal")
            sys_widget.insert("end", f"[{tab_name}] {message}\n", "error")
            sys_widget.see("end")
            sys_widget.configure(state="disabled")

    def log_result(self, message, tag="data"):
        self.result_box.configure(state="normal")
        self.result_box.insert("end", f"{message}\n", tag)
        self.result_box.see("end")
        self.result_box.configure(state="disabled")

    def run_command(self, cmd, cwd, tag_name="System", log_target="System", env=None):
        def task():
            try:
                self.log(log_target, f"执行指令: {' '.join(cmd)}", "info")
                if not os.path.exists(cwd): return
                final_env = os.environ.copy()
                if env: final_env.update(env)
                p = subprocess.Popen(cmd, cwd=cwd, env=final_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding="utf-8", errors="replace")
                buf = []
                for line in iter(p.stdout.readline, ''):
                    l = line.strip()
                    if l: 
                        self.log(log_target, l, "info")
                        buf.append(l)
                p.wait()
                if tag_name == "Deploy": self.deployment_output = "\n".join(buf)
                if p.returncode == 0: self.log(log_target, "执行成功。", "success")
                else: self.log(log_target, f"执行失败 (代码 {p.returncode})", "error")
            except Exception as e: self.log(log_target, f"异常: {e}", "error")
        threading.Thread(target=task, daemon=True).start()

    def load_json_tolerant(self, file_path):
        if not os.path.exists(file_path): raise FileNotFoundError(f"Missing: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
        try: return json.loads(content)
        except json.JSONDecodeError:
            fixed = re.sub(r',(\s*[}\]])', r'\1', content)
            fixed = re.sub(r'(["}\]])\s*\n\s*(")', r'\1,\n\2', fixed)
            last_brace = fixed.rfind('}')
            if last_brace != -1: fixed = fixed[:last_brace+1]
            try:
                data = json.loads(fixed)
                with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)
                return data
            except: raise Exception("配置文件修复失败")

    def check_consistency(self):
        json_path = os.path.join(BUILD_DIR, "OracleContract.json")
        if not os.path.exists(json_path): return False, "请先部署合约。"
        try:
            with open(json_path, 'r') as f: 
                build_data = json.load(f)
                networks = build_data.get("networks", {})
                if not networks: return False, "Build 文件中无网络信息"
                latest_id = list(networks.keys())[-1]
                addr = networks[latest_id]["address"]
        except Exception as e: return False, f"读取错误: {e}"
        
        node_path = os.path.join(CONFIG_DIR, "node1.json")
        try:
            data = self.load_json_tolerant(node_path)
            node_addr = data["contracts"].get("oracleContractAddress")
        except: return False, "节点配置读取错误"

        if addr.lower() != node_addr.lower(): return False, f"地址不匹配!\n部署地址: {addr}\n节点配置: {node_addr}"
        return True, "OK"

    def kill_all_nodes(self):
        self.log("System", ">>> 正在清理旧进程...", "info")
        subprocess.run(["pkill", "-f", "ioporaclenode"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.node_processes.clear()
        time.sleep(1) 
        self.log("System", "清理完成。", "success")

    def deploy_contracts(self):
        self.log("System", ">>> 正在部署合约...", "info")
        self.run_command(["truffle", "migrate", "--reset"], cwd=CONTRACTS_DIR, tag_name="Deploy")

    def compile_node(self):
        self.log("System", ">>> 正在编译节点...", "info")
        cmd = ["go", "build", "-a", "-o", "ioporaclenode", "cmd/ioporaclenode/main.go"]
        def task():
            p = subprocess.Popen(cmd, cwd=NODE_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding="utf-8", errors="replace")
            p.communicate()
            if p.returncode == 0: self.log("System", "✅ 编译成功。", "success")
            else: self.log("System", "编译失败。", "error")
        threading.Thread(target=task, daemon=True).start()

    def auto_fill_addresses(self):
        if not self.deployment_output: return messagebox.showwarning("警告", "请先部署合约。")
        matches = re.findall(r"> contract address:\s*(0x[a-fA-F0-9]{40})", self.deployment_output)
        if len(matches) < 3: return self.log("System", "❌ 未找到合约地址。", "error")
        
        addr_map = {"distKeyContractAddress": matches[-3], "registryContractAddress": matches[-2], "oracleContractAddress": matches[-1]}
        n = int(self.node_count_var.get())
        
        self.log("System", ">>> 正在更新配置文件...", "info")
        for i in range(1, n + 1):
            cfg_path = os.path.join(CONFIG_DIR, f"node{i}.json")
            if os.path.exists(cfg_path):
                try:
                    data = self.load_json_tolerant(cfg_path)
                    if "contracts" not in data: data["contracts"] = {}
                    data["contracts"].update(addr_map)
                    if "ethereum" in data: 
                         for k in ["sourceAddress", "targetAddress"]:
                             if k in data["ethereum"] and "http" in data["ethereum"][k]:
                                 data["ethereum"][k] = data["ethereum"][k].replace("http", "ws")
                    with open(cfg_path, 'w') as f: json.dump(data, f, indent=4)
                except Exception as e: self.log("System", f"节点 {i} 更新失败: {e}", "error")
        self.log("System", "✅ 配置更新完毕。", "success")
        messagebox.showinfo("成功", "地址回填成功！")

    def open_key_config_window(self):
        n = int(self.node_count_var.get())
        d = ctk.CTkToplevel(self)
        d.title("配置 Ganache 私钥")
        d.geometry("600x500")
        d.attributes("-topmost", True)
        sf = ctk.CTkScrollableFrame(d)
        sf.pack(fill="both", expand=True, padx=10, pady=10)
        entries = []
        for i in range(1, n+1):
            f = ctk.CTkFrame(sf)
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=f"节点 {i}:", width=50).pack(side="left")
            e = ctk.CTkEntry(f, width=400)
            e.pack(side="left", fill="x", expand=True)
            try:
                data = self.load_json_tolerant(os.path.join(CONFIG_DIR, f"node{i}.json"))
                eth_key = data.get("ethereum", {}).get("privateKey", "未配置")
                e.insert(0, eth_key)
            except: pass
            entries.append((i, e))
        def save():
            for i, e in entries:
                try:
                    p = os.path.join(CONFIG_DIR, f"node{i}.json")
                    d = self.load_json_tolerant(p)
                    if "ethereum" not in d: d["ethereum"] = {}
                    d["ethereum"]["privateKey"] = e.get().strip()
                    with open(p, 'w') as f: json.dump(d, f, indent=4)
                except: pass
            d.destroy()
            messagebox.showinfo("成功", "私钥已保存！")
        ctk.CTkButton(d, text="保存配置", command=save, fg_color="green").pack(pady=10)

    def start_nodes(self):
        self.kill_all_nodes()
        n = int(self.node_count_var.get())
        self.log("System", f"========== 启动 {n} 个节点 ==========", "info")
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.configure(state="disabled")

        def launch():
            for i in range(1, n + 1):
                time.sleep(1.5)
                cmd = ["./ioporaclenode", "-c", f"configs/node{i}.json"]
                rpc = "Unknown"
                try: rpc = self.load_json_tolerant(os.path.join(CONFIG_DIR, f"node{i}.json"))["ethereum"]["sourceAddress"]
                except: pass

                def monitor(node_id, p, rpc_url):
                    tab = f"节点 {node_id}"
                    self.log(tab, f"启动成功 ({rpc_url})", "success")
                    for line in iter(p.stdout.readline, ''):
                        l = line.strip()
                        if not l: continue
                        lower = l.lower()
                        if "bind: address already in use" in lower: self.log(tab, f"端口占用: {l}", "error")
                        elif "fatal" in lower or "panic" in lower: self.log(tab, l, "error")
                        else: self.log(tab, l, "info")

                        if "S:" in l: 
                            try: self.captured_s = l.split("S:")[1].strip()
                            except: pass
                            self.log_result(f"  {l}", "data")
                        elif "R:" in l:
                            try: self.captured_r = l.split("R:")[1].strip()
                            except: pass
                            self.log_result(f"  {l}", "data")
                        elif ">>> 该节点签名" in l: self.log_result(f"\n{l}", "header_node")
                        elif ">>> 总签名" in l: self.log_result(f"\n========================================\n{l}", "header_total")
                        elif "--- 步骤" in l: self.log_result(l, "step")
                        elif "节点地址:" in l: self.log_result(f"  {l}", "data")
                        elif "------" in l: self.log_result(l, "data")
                    p.wait()
                    self.log(tab, "已退出。", "info")

                try:
                    self.log("System", f"正在启动节点 {i} ...", "info")
                    p = subprocess.Popen(cmd, cwd=NODE_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding="utf-8", errors="replace")
                    self.node_processes[i] = p
                    threading.Thread(target=monitor, args=(i, p, rpc), daemon=True).start()
                except Exception as e: self.log("System", f"启动失败: {e}", "error")
            self.log("System", "✅ 所有节点启动完毕。", "success")
        threading.Thread(target=launch, daemon=True).start()

    def select_file(self):
        f = filedialog.askopenfilename(initialdir=BASE_DIR)
        if f:
            self.selected_file_path = f
            self.lbl_file.configure(text=os.path.basename(f), text_color="cyan")
            self.log("System", f"已选择文件: {f}", "info")

    def create_trigger_js(self, file_path):
        js = r"""
const fs = require('fs');
const OracleContract = artifacts.require("OracleContract");
module.exports = async function(callback) {
  try {
    const filePath = process.env.TARGET_FILE_PATH;
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const fileHash = web3.utils.sha3(fileContent);
    const fee = web3.utils.toWei("0.0012", "ether");
    const oracle = await OracleContract.deployed();
    console.log("--------------------------------------------");
    console.log("🚀 GUI Trigger: Validating File");
    console.log("📄 Hash:", fileHash);
    console.log("--------------------------------------------");
    const tx = await oracle.validateBlock(fileHash, { value: fee });
    console.log("✅ Transaction Sent! Hash:", tx.tx);
    console.log("👉 Waiting for signatures...");
  } catch (error) { console.error("❌ Error:", error); }
  callback();
};
"""
        p = os.path.join(SCRIPTS_DIR, "gui_trigger_sign.js")
        with open(p, "w", encoding="utf-8") as f: f.write(js)
        return p

    def create_submit_proof_js(self):
        # [核心修复: 自动充值合约 + 中文日志]
        js = r"""
const OracleContract = artifacts.require("OracleContract");
module.exports = async function(callback) {
  try {
    const fileHash = process.env.TARGET_HASH;
    let sStr = process.env.TARGET_S || ""; 
    let rStr = process.env.TARGET_R || ""; 

    if (!fileHash || !sStr || !rStr) {
        console.error("❌ 缺少签名数据 (Hash/S/R)，请先执行步骤9！");
        return callback();
    }

    const oracle = await OracleContract.deployed();
    const accounts = await web3.eth.getAccounts();
    const funder = accounts[0];

    // === 1. 自动为合约充值 (解决 Transfer Failed) ===
    // 检查合约余额，如果不足 1 ETH，则充值 10 ETH
    const balance = await web3.eth.getBalance(oracle.address);
    if (web3.utils.toBN(balance).lt(web3.utils.toBN(web3.utils.toWei("1", "ether")))) {
        console.log("💰 正在为合约充值 10 ETH 以便支付奖励...");
        await web3.eth.sendTransaction({
            from: funder,
            to: oracle.address,
            value: web3.utils.toWei("10", "ether")
        });
        console.log("✅ 合约充值成功。");
    }

    // === 2. 数据清洗与切分 ===
    const sClean = sStr.replace(/0x/g, "").replace(/[^0-9a-fA-F]/g, "");
    const rClean = rStr.replace(/0x/g, "").replace(/[^0-9a-fA-F]/g, "");
    
    const sigStruct = {
        S: [
            "0x" + (sClean.substring(0, 64) || "0"),
            "0x" + (sClean.substring(64, 128) || "0")
        ],
        R: [
            "0x" + (rClean.substring(0, 64) || "0"),
            "0x" + (rClean.substring(64, 128) || "0"),
            "0x" + (rClean.substring(128, 192) || "0"),
            "0x" + (rClean.substring(192, 256) || "0")
        ]
    };

    console.log("============================================");
    console.log("🚀 正在上链存证 (submitBlockValidationIBOS)");
    console.log("--------------------------------------------");
    console.log("📄 文件哈希:", fileHash);

    const tx = await oracle.submitBlockValidationIBOS(
        fileHash,
        true, 
        [web3.utils.utf8ToHex("Node1")], 
        [sigStruct], 
        Date.now() 
    );

    console.log("✅ 上链成功! 交易哈希:", tx.tx);
    console.log("FINAL_SUCCESS_FLAG"); 

  } catch (error) {
    console.error("❌ 错误:", error);
  }
  callback();
};
"""
        p = os.path.join(SCRIPTS_DIR, "submit_proof.js")
        with open(p, "w", encoding="utf-8") as f: f.write(js)
        return p

    def start_signing(self):
        if not self.selected_file_path: return messagebox.showerror("错误", "请先选择文件")
        ok, msg = self.check_consistency()
        if not ok: return messagebox.showerror("错误", msg)

        self.final_hash = ""
        self.captured_s = ""
        self.captured_r = ""

        self.log("System", ">>> 正在发起签名...", "sign")
        self.log_result(f">>> 开始对文件 {os.path.basename(self.selected_file_path)} 进行处理...", "trigger")
        
        try: js = self.create_trigger_js(self.selected_file_path)
        except: return
        
        cmd = ["truffle", "exec", "scripts/gui_trigger_sign.js", "--network", "development"]
        env = {"TARGET_FILE_PATH": self.selected_file_path}
        
        def run_trigger():
            try:
                p = subprocess.Popen(cmd, cwd=CONTRACTS_DIR, env={**os.environ, **env}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
                for line in iter(p.stdout.readline, ''):
                    l = line.strip()
                    if l:
                        self.log("System", l, "info")
                        if "Hash:" in l and "0x" in l:
                            self.final_hash = l.split("Hash:")[1].strip()
                p.wait()
            except: pass
        
        threading.Thread(target=run_trigger, daemon=True).start()
        self.log("System", "请求已发送，等待节点响应...", "info")

    def start_proof_submission(self):
        if not self.final_hash: return messagebox.showwarning("等待", "哈希尚未生成")
        if not self.captured_s: return messagebox.showwarning("等待", "尚未捕获到聚合签名")

        self.log("System", ">>> 正在启动上链存证...", "sign")
        try: self.create_submit_proof_js()
        except: return

        cmd = ["truffle", "exec", "scripts/submit_proof.js", "--network", "development"]
        env = {
            "TARGET_HASH": self.final_hash,
            "TARGET_S": self.captured_s,
            "TARGET_R": self.captured_r
        }

        def run_proof():
            try:
                p = subprocess.Popen(cmd, cwd=CONTRACTS_DIR, env={**os.environ, **env}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
                success = False
                for line in iter(p.stdout.readline, ''):
                    l = line.strip()
                    if l:
                        if "FINAL_SUCCESS_FLAG" in l: success = True
                        self.log("System", l, "info")
                p.wait()
                if success:
                    self.log_result("\n############################################", "final_success")
                    self.log_result(f"📄 文件哈希: {self.final_hash}", "data")
                    self.log_result(f"🔑 聚合签名 S: {self.captured_s[:30]}...", "data")
                    self.log_result("✅ 聚合验证成功 (已上链存证)", "final_success")
                    self.log_result("############################################\n", "final_success")
                    messagebox.showinfo("成功", "验证成功并已上链！")
            except: pass
        threading.Thread(target=run_proof, daemon=True).start()

if __name__ == "__main__":
    app = SystemGUI()
    app.mainloop()
