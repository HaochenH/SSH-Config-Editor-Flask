from flask import Flask, render_template_string, request, jsonify
import os
import platform

app = Flask(__name__)

# Windows and Unix path compatibility
if platform.system() == 'Windows':
    SSH_CONFIG_PATH = os.path.expanduser("~\\.ssh\\config")
else:
    SSH_CONFIG_PATH = os.path.expanduser("~/.ssh/config")

def parse_ssh_config(content):
    """Parse SSH config file into a list"""
    hosts = []
    current_host = None
    
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = line.split(None, 1)
        if not parts:
            continue
        
        key = parts[0].lower()
        value = parts[1] if len(parts) > 1 else ""
        
        if key == 'host':
            if current_host:
                hosts.append(current_host)
            current_host = {'name': value, 'options': {}}
        elif current_host:
            current_host['options'][key] = value
    
    if current_host:
        hosts.append(current_host)
    
    return hosts

def generate_ssh_config(hosts):
    """Convert host list to SSH config format"""
    lines = []
    for host in hosts:
        lines.append(f"Host {host['name']}")
        for key, value in host['options'].items():
            lines.append(f"    {key} {value}")
        lines.append("")
    return '\n'.join(lines)

@app.route('/')
def index():
    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SSH-Config-Editor-Flask</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Roboto', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #fafafa; min-height: 100vh; padding: 24px; }
        .container { max-width: 1000px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden; }
        .header { background: white; padding: 24px; border-bottom: 1px solid #e0e0e0; border-radius: 12px 12px 0 0; }
        .header h1 { font-size: 24px; font-weight: 500; color: #212121; margin-bottom: 4px; letter-spacing: -0.5px; }
        .header p { color: #757575; font-size: 14px; font-weight: 400; }
        .content { padding: 24px; }
        .button-group { display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }
        button { padding: 10px 16px; border: none; cursor: pointer; font-size: 14px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); font-family: 'Roboto', sans-serif; }
        button:not(.tab-button) { border-radius: 6px; }
        .btn-primary { background: white; color: #1976d2; border: 1px solid #bdbdbd; }
        .btn-primary:hover { background: #f5f5f5; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .btn-success { background: #4caf50; color: white; }
        .btn-success:hover { background: #45a049; box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3); }
        .btn-danger { background: white; color: #f44336; border: 1px solid #bdbdbd; }
        .btn-danger:hover { background: #ffebee; border-color: #f44336; }
        .btn-small { padding: 6px 12px; font-size: 12px; }
        .host-card { background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin-bottom: 12px; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); cursor: grab; user-select: none; }
        .host-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.12), 0 2px 4px rgba(0,0,0,0.08); border-color: #bdbdbd; }
        .host-card.dragging { opacity: 0.5; background: #f5f5f5; }
        .host-card.drag-over { box-shadow: 0 4px 16px rgba(25, 118, 210, 0.2); border-color: #1976d2; border-width: 2px; }
        .drag-handle { display: inline-block; color: #9e9e9e; margin-right: 8px; cursor: grab; font-size: 16px; }
        .host-name { font-size: 16px; font-weight: 500; color: #212121; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
        .host-options { display: grid; gap: 12px; margin-bottom: 12px; }
        .option-row { display: grid; grid-template-columns: 1fr 2fr auto; gap: 12px; align-items: center; }
        .add-option-section { display: grid; grid-template-columns: 1fr 1fr auto; gap: 12px; align-items: center; padding-top: 12px; border-top: 1px solid #e0e0e0; }
        .add-option-section select, .add-option-section input, .option-row input { padding: 8px 12px; border: 1px solid #bdbdbd; border-radius: 6px; font-size: 13px; font-family: 'Roboto', sans-serif; }
        .add-option-section select:focus, .add-option-section input:focus, .option-row input:focus { outline: none; border-color: #1976d2; box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.1); }
        .option-row input:disabled { background: #fafafa; color: #9e9e9e; cursor: not-allowed; }
        .modal { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.32); z-index: 1000; align-items: center; justify-content: center; }
        .modal.active { display: flex; }
        .modal-content { background: white; padding: 24px; border-radius: 12px; max-width: 500px; width: 90%; box-shadow: 0 5px 25px -8px rgba(0,0,0,0.3); }
        .modal-content h2 { margin-bottom: 16px; color: #212121; font-size: 20px; font-weight: 500; }
        .form-group { margin-bottom: 16px; }
        .form-group label { display: block; margin-bottom: 8px; color: #212121; font-size: 13px; font-weight: 500; }
        .form-group input { width: 100%; padding: 10px 12px; border: 1px solid #bdbdbd; border-radius: 6px; font-size: 14px; font-family: 'Roboto', sans-serif; }
        .modal-buttons { display: flex; gap: 8px; margin-top: 24px; justify-content: flex-end; }
        .message { padding: 12px 16px; border-radius: 2px; margin-bottom: 16px; display: none; font-size: 14px; }
        .message.show { display: block; }
        .message.success { background: #e8f5e9; color: #1b5e20; border-left: 4px solid #4caf50; }
        .message.error { background: #ffebee; color: #b71c1c; border-left: 4px solid #f44336; }
        .tabs-wrapper { border-bottom: 1px solid #e0e0e0; margin-bottom: 24px; }
        .tabs { display: flex; gap: 0; }
        .tab-button { padding: 16px 24px; border: none; background: transparent; color: #757575; cursor: pointer; border-bottom: 2px solid transparent; font-size: 14px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); }
        .tab-button:hover { color: #212121; }
        .tab-button.active { color: #1976d2; border-bottom-color: #1976d2; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .raw-editor { background: #263238; color: #aed581; padding: 16px; border-radius: 8px; font-family: 'Roboto Mono', monospace; font-size: 12px; line-height: 1.6; border: 1px solid #37474f; min-height: 400px; width: 100%; resize: vertical; box-sizing: border-box; }
        .raw-editor:focus { outline: none; box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.1); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SSH-Config-Editor-Flask</h1>
        </div>
        
        <div class="content">
            <div class="message" id="message"></div>
            
            <div class="tabs-wrapper">
                <div class="tabs">
                    <button class="tab-button active" onclick="switchTab(event, 'editor')">Editor</button>
                    <button class="tab-button" onclick="switchTab(event, 'raw')">Raw File</button>
                </div>
            </div>
            
            <div class="button-group">
                <button class="btn-success" onclick="saveConfig()">Save</button>
                <button class="btn-primary" onclick="loadConfig()">Refresh</button>
                <button class="btn-primary" onclick="showAddHostModal()">Add Host</button>
            </div>
            
            <div id="editor-content" class="tab-content active">
                <div class="hosts-list" id="hostsList"></div>
            </div>
            
            <div id="raw-content" class="tab-content">
                <textarea class="raw-editor" id="rawEditor" placeholder="Paste or edit SSH config file content..."></textarea>
                <div style="margin-top: 12px; display: flex; gap: 8px;">
                    <button class="btn-success" onclick="saveRawConfig()">Save Raw File</button>
                    <button class="btn-primary" onclick="loadRawConfig()">Load from File</button>
                </div>
            </div>
        </div>
    </div>
    
    <div class="modal" id="addHostModal">
        <div class="modal-content">
            <h2>Add New Host</h2>
            <div class="form-group">
                <label>Host Name/Alias *</label>
                <input type="text" id="newHostName" placeholder="e.g.: myserver">
            </div>
            <div class="form-group">
                <label>HostName</label>
                <input type="text" id="newHostHostname" placeholder="e.g.: 192.168.1.100 or example.com">
            </div>
            <div class="form-group">
                <label>User</label>
                <input type="text" id="newHostUser" placeholder="e.g.: ubuntu">
            </div>
            <div class="form-group">
                <label>Port</label>
                <input type="text" id="newHostPort" placeholder="Default: 22">
            </div>
            <div class="form-group">
                <label>IdentityFile</label>
                <input type="text" id="newHostIdentity" placeholder="e.g.: ~/.ssh/id_rsa">
            </div>
            <div class="modal-buttons">
                <button class="btn-primary" onclick="closeAddHostModal()">Cancel</button>
                <button class="btn-success" onclick="addHost()">Add</button>
            </div>
        </div>
    </div>
    
    <script>
        let hosts = [];
        let draggedIndex = null;
        
        function loadConfig() {
            fetch('/api/config').then(r => r.json()).then(data => {
                hosts = data.hosts;
                renderHosts();
                showMessage('Configuration loaded', 'success');
            }).catch(err => showMessage('Load failed: ' + err, 'error'));
        }
        
        function renderHosts() {
            const listEl = document.getElementById('hostsList');
            if (hosts.length === 0) {
                listEl.innerHTML = '<p style="color: #a0aec0; text-align: center; padding: 40px;">No hosts configured yet</p>';
                return;
            }
            
            listEl.innerHTML = hosts.map((host, idx) => {
                const optionsHtml = Object.entries(host.options).map(([key, value]) => `
                    <div class="option-row">
                        <input type="text" value="${key}" disabled style="background: #fafafa;">
                        <input type="text" value="${value}" onchange="updateOption(${idx}, '${key}', this.value)">
                        <button class="btn-danger btn-small" onclick="deleteOption(${idx}, '${key}')">Delete</button>
                    </div>
                `).join('');
                
                return `
                    <div class="host-card" draggable="true" data-index="${idx}" ondragstart="dragStart(event)" ondragend="dragEnd(event)" ondragover="dragOver(event)" ondrop="drop(event)">
                        <div class="host-name">
                            <span><span class="drag-handle">⋮⋮</span>${host.name}</span>
                            <button class="btn-danger btn-small" onclick="deleteHost(${idx})">Delete</button>
                        </div>
                        <div class="host-options">${optionsHtml}</div>
                        <div class="add-option-section">
                            <select id="optionSelect_${idx}" onchange="onOptionSelectChange(${idx})">
                                <option value="">Add...</option>
                                <option value="HostName">HostName</option>
                                <option value="User">User</option>
                                <option value="Port">Port</option>
                                <option value="IdentityFile">IdentityFile</option>
                                <option value="ProxyCommand">ProxyCommand</option>
                                <option value="ProxyJump">ProxyJump</option>
                                <option value="LocalForward">LocalForward</option>
                                <option value="RemoteForward">RemoteForward</option>
                                <option value="custom">Custom...</option>
                            </select>
                            <input type="text" id="optionValue_${idx}" placeholder="Enter value" onkeypress="if(event.key==='Enter') addOption(${idx})"></input>
                            <button class="btn-success btn-small" onclick="addOption(${idx})">Add</button>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function updateOption(idx, key, value) { hosts[idx].options[key] = value; }
        function deleteHost(idx) { if (confirm('Are you sure you want to delete?')) { hosts.splice(idx, 1); renderHosts(); } }
        function deleteOption(idx, key) { delete hosts[idx].options[key]; renderHosts(); }
        
        function onOptionSelectChange(idx) {
            const selectEl = document.getElementById(`optionSelect_${idx}`);
            if (selectEl.value === 'custom') {
                const customKey = prompt('Enter custom option name:');
                if (customKey) {
                    selectEl.value = customKey;
                    document.getElementById(`optionValue_${idx}`).focus();
                } else {
                    selectEl.value = '';
                }
            }
        }
        
        function addOption(idx) {
            const selectEl = document.getElementById(`optionSelect_${idx}`);
            const valueEl = document.getElementById(`optionValue_${idx}`);
            let key = selectEl.value;
            const value = valueEl.value.trim();
            
            if (!key || !value) {
                showMessage('Please select an option and enter a value', 'error');
                return;
            }
            
            hosts[idx].options[key] = value;
            selectEl.value = '';
            valueEl.value = '';
            renderHosts();
            showMessage('Option added', 'success');
        }
        
        function showAddHostModal() { document.getElementById('addHostModal').classList.add('active'); }
        function closeAddHostModal() {
            document.getElementById('addHostModal').classList.remove('active');
            document.getElementById('newHostName').value = '';
            document.getElementById('newHostHostname').value = '';
            document.getElementById('newHostUser').value = '';
            document.getElementById('newHostPort').value = '';
            document.getElementById('newHostIdentity').value = '';
        }
        
        function addHost() {
            const name = document.getElementById('newHostName').value.trim();
            if (!name) { showMessage('Please enter a host name', 'error'); return; }
            
            const options = {};
            const hostname = document.getElementById('newHostHostname').value.trim();
            const user = document.getElementById('newHostUser').value.trim();
            const port = document.getElementById('newHostPort').value.trim();
            const identity = document.getElementById('newHostIdentity').value.trim();
            
            if (hostname) options.HostName = hostname;
            if (user) options.User = user;
            if (port) options.Port = port;
            if (identity) options.IdentityFile = identity;
            
            hosts.push({name, options});
            renderHosts();
            closeAddHostModal();
            showMessage('Host added', 'success');
        }
        
        function saveConfig() {
            fetch('/api/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({hosts})
            }).then(r => r.json()).then(data => {
                if (data.success) showMessage('Configuration saved', 'success');
                else showMessage('Save failed: ' + data.error, 'error');
            }).catch(err => showMessage('Save failed: ' + err, 'error'));
        }
        
        function showMessage(text, type) {
            const msg = document.getElementById('message');
            msg.textContent = text;
            msg.className = 'message show ' + type;
            setTimeout(() => msg.classList.remove('show'), 3000);
        }
        
        function switchTab(e, tab) {
            e.preventDefault();
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.getElementById(tab + '-content').classList.add('active');
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
            if (tab === 'raw') loadRawConfig();
        }
        
        function loadRawConfig() {
            fetch('/api/config').then(r => r.json()).then(data => {
                hosts = data.hosts;
                fetch('/api/raw-config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({hosts})
                }).then(r => r.json()).then(data => {
                    document.getElementById('rawEditor').value = data.config;
                });
            });
        }
        
        function saveRawConfig() {
            const content = document.getElementById('rawEditor').value;
            fetch('/api/save-raw', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({content})
            }).then(r => r.json()).then(data => {
                if (data.success) { showMessage('Saved', 'success'); loadConfig(); }
                else showMessage('Save failed: ' + data.error, 'error');
            }).catch(err => showMessage('Save failed: ' + err, 'error'));
        }
        
        function dragStart(event) {
            draggedIndex = parseInt(event.target.closest('.host-card').dataset.index);
            event.target.closest('.host-card').classList.add('dragging');
        }
        
        function dragEnd(event) {
            document.querySelectorAll('.host-card').forEach(card => {
                card.classList.remove('dragging');
                card.classList.remove('drag-over');
            });
        }
        
        function dragOver(event) {
            event.preventDefault();
            const card = event.target.closest('.host-card');
            if (card && draggedIndex !== null) card.classList.add('drag-over');
        }
        
        function drop(event) {
            event.preventDefault();
            const card = event.target.closest('.host-card');
            if (!card) return;
            const dropIndex = parseInt(card.dataset.index);
            if (draggedIndex !== null && draggedIndex !== dropIndex) {
                const draggedHost = hosts.splice(draggedIndex, 1)[0];
                const newIndex = draggedIndex < dropIndex ? dropIndex - 1 : dropIndex;
                hosts.splice(newIndex, 0, draggedHost);
                renderHosts();
            }
            document.querySelectorAll('.host-card').forEach(c => c.classList.remove('drag-over'));
        }
        
        loadConfig();
    </script>
</body>
</html>'''
    return render_template_string(html)

@app.route('/api/config')
def get_config():
    try:
        if os.path.exists(SSH_CONFIG_PATH):
            with open(SSH_CONFIG_PATH, 'r') as f:
                content = f.read()
        else:
            content = ""
        hosts = parse_ssh_config(content)
        return jsonify({'hosts': hosts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/raw-config', methods=['POST'])
def get_raw_config():
    try:
        data = request.json
        hosts = data.get('hosts', [])
        config = generate_ssh_config(hosts)
        return jsonify({'config': config})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save', methods=['POST'])
def save_config():
    try:
        data = request.json
        hosts = data.get('hosts', [])
        config = generate_ssh_config(hosts)
        
        ssh_dir = os.path.dirname(SSH_CONFIG_PATH)
        os.makedirs(ssh_dir, exist_ok=True)
        with open(SSH_CONFIG_PATH, 'w') as f:
            f.write(config)
        
        if platform.system() != 'Windows':
            os.chmod(SSH_CONFIG_PATH, 0o600)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/save-raw', methods=['POST'])
def save_raw_config():
    try:
        data = request.json
        content = data.get('content', '')
        
        ssh_dir = os.path.dirname(SSH_CONFIG_PATH)
        os.makedirs(ssh_dir, exist_ok=True)
        with open(SSH_CONFIG_PATH, 'w') as f:
            f.write(content)
        
        if platform.system() != 'Windows':
            os.chmod(SSH_CONFIG_PATH, 0o600)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    if platform.system() == 'Windows':
        try:
            from waitress import serve
            print('SSH Config Editor running at http://localhost:5000')
            print('Press Ctrl+C to stop the service')
            serve(app, host='127.0.0.1', port=5000)
        except ImportError:
            print('Need to install waitress: pip install waitress')
            app.run(host='127.0.0.1', port=5000, use_reloader=False)
    else:
        app.run(debug=True, port=5000)