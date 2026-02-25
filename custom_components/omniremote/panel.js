/**
 * OmniRemote Manager Panel v1.5.3
 * Uses event delegation for reliable button handling in Shadow DOM
 */

const OMNIREMOTE_VERSION = "1.5.5";

class OmniRemotePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._data = { rooms: [], devices: [], scenes: [], blasters: [], haBlasters: [], catalog: [] };
    this._view = 'dashboard';
    this._modal = null;
    this._roomId = null;
    this._deviceId = null;
    this._version = OMNIREMOTE_VERSION;
  }

  set hass(hass) {
    const firstTime = !this._hass;
    this._hass = hass;
    if (firstTime) {
      this._render();
      this._loadData();
      this._checkVersion();
    }
  }

  async _checkVersion() {
    try {
      const res = await this._api('/api/omniremote/version');
      if (res.version && res.version !== this._version) {
        console.warn(`[OmniRemote] Version mismatch! Panel: ${this._version}, Server: ${res.version}`);
        this._versionMismatch = res.version;
        this._render();
      }
    } catch (e) {
      console.debug('[OmniRemote] Version check failed:', e);
    }
  }

  async _loadData() {
    console.log('[OmniRemote] Loading data...');
    try {
      const results = await Promise.all([
        this._api('/api/omniremote/rooms'),
        this._api('/api/omniremote/devices'),
        this._api('/api/omniremote/scenes'),
        this._api('/api/omniremote/blasters'),
        this._api('/api/omniremote/catalog'),
      ]);
      
      this._data = {
        rooms: results[0]?.rooms || [],
        devices: results[1]?.devices || [],
        scenes: results[2]?.scenes || [],
        haEntities: results[2]?.ha_entities || [],
        blasters: results[3]?.blasters || [],
        haBlasters: results[3]?.ha_blasters || [],
        catalog: results[4]?.devices || [],
        dbOk: results[3]?.database_available !== false,
      };
      
      console.log('[OmniRemote] Data loaded:', this._data);
      this._render();
    } catch (e) {
      console.error('[OmniRemote] Load error:', e);
    }
  }

  async _api(url, method = 'GET', body = null) {
    const headers = { 'Content-Type': 'application/json' };
    
    // Add HA auth token if available
    if (this._hass && this._hass.auth && this._hass.auth.data) {
      headers['Authorization'] = `Bearer ${this._hass.auth.data.access_token}`;
    }
    
    const opts = { 
      method, 
      headers,
      credentials: 'same-origin' 
    };
    if (body) opts.body = JSON.stringify(body);
    
    console.log(`[OmniRemote] API ${method} ${url}`, body || '');
    
    try {
      const res = await fetch(url, opts);
      
      // Check if response is OK
      if (!res.ok) {
        console.error(`[OmniRemote] API error status: ${res.status}`);
        return { error: `HTTP ${res.status}: ${res.statusText}` };
      }
      
      // Get response text first to handle non-JSON responses
      const text = await res.text();
      
      // Try to parse as JSON
      try {
        const json = JSON.parse(text);
        console.log(`[OmniRemote] API response:`, json);
        return json;
      } catch (parseError) {
        console.error(`[OmniRemote] JSON parse error:`, parseError, 'Response text:', text.substring(0, 200));
        return { error: `Invalid JSON response: ${text.substring(0, 100)}` };
      }
    } catch (e) {
      console.error(`[OmniRemote] API fetch error:`, e);
      return { error: e.message };
    }
  }

  _render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; height:100%; font-family:system-ui,-apple-system,sans-serif; }
        * { box-sizing:border-box; }
        .app { display:flex; height:100vh; background:#0f0f1a; color:#e8e8e8; }
        
        /* Sidebar */
        .sidebar { width:220px; background:#1a1a2e; border-right:1px solid #2a2a4a; display:flex; flex-direction:column; }
        .logo { padding:16px; font-weight:600; display:flex; align-items:center; gap:8px; border-bottom:1px solid #2a2a4a; }
        .logo ha-icon { color:#03a9f4; }
        .logo-text { display:flex; flex-direction:column; }
        .logo-title { font-size:14px; }
        .logo-version { font-size:10px; color:#888; font-weight:400; }
        .nav { flex:1; padding:8px 0; overflow-y:auto; }
        .nav-item { display:flex; align-items:center; gap:10px; padding:10px 16px; cursor:pointer; border-left:3px solid transparent; }
        .nav-item:hover { background:#252545; }
        .nav-item.active { background:#252545; border-left-color:#03a9f4; }
        .nav-item ha-icon { color:#888; width:20px; }
        .nav-item.active ha-icon { color:#03a9f4; }
        .nav-item .badge { margin-left:auto; background:#03a9f4; color:#fff; padding:2px 8px; border-radius:10px; font-size:11px; }
        .nav-section { padding:8px 16px 4px; font-size:10px; text-transform:uppercase; color:#666; letter-spacing:1px; margin-top:8px; }
        .nav-item.add-room { color:#03a9f4; }
        
        /* Main */
        .main { flex:1; display:flex; flex-direction:column; overflow:hidden; }
        .header { padding:16px 24px; background:#1a1a2e; border-bottom:1px solid #2a2a4a; display:flex; justify-content:space-between; align-items:center; }
        .header h2 { margin:0; font-size:20px; font-weight:500; }
        .content { flex:1; padding:24px; overflow-y:auto; }
        
        /* Buttons */
        .btn { display:inline-flex; align-items:center; gap:6px; padding:8px 16px; border:none; border-radius:8px; cursor:pointer; font-size:13px; font-weight:500; }
        .btn ha-icon { --mdc-icon-size:16px; }
        .btn-p { background:#03a9f4; color:#fff; }
        .btn-p:hover { background:#0288d1; }
        .btn-s { background:#252545; color:#e8e8e8; }
        .btn-s:hover { background:#303060; }
        .btn-d { background:#c62828; color:#fff; }
        
        /* Cards */
        .grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:16px; }
        .card { background:#1a1a2e; border:1px solid #2a2a4a; border-radius:12px; padding:16px; }
        .card-head { display:flex; align-items:center; gap:12px; }
        .card-icon { width:40px; height:40px; border-radius:10px; background:#252545; display:flex; align-items:center; justify-content:center; }
        .card-icon ha-icon { color:#03a9f4; }
        .card-info { flex:1; }
        .card-title { font-weight:500; }
        .card-sub { font-size:12px; color:#888; margin-top:2px; }
        .card-btns { margin-top:12px; display:flex; gap:8px; }
        
        /* Stats */
        .stats { display:flex; gap:16px; margin-bottom:24px; flex-wrap:wrap; }
        .stat { background:#1a1a2e; border:1px solid #2a2a4a; border-radius:12px; padding:16px 20px; min-width:120px; }
        .stat-val { font-size:28px; font-weight:600; color:#03a9f4; }
        .stat-lbl { font-size:12px; color:#888; margin-top:4px; }
        
        /* Empty */
        .empty { text-align:center; padding:60px 20px; color:#888; }
        .empty ha-icon { --mdc-icon-size:48px; opacity:0.5; }
        .empty h3 { color:#e8e8e8; margin:16px 0 8px; }
        .empty p { margin:0 0 20px; }
        
        /* Warning */
        .warning { background:#3d2e00; border:1px solid #ff9800; border-radius:12px; padding:16px; margin-bottom:24px; display:flex; align-items:center; gap:12px; }
        
        /* Version Banner */
        .version-banner { background:#1a3d1a; border:1px solid #4caf50; padding:12px 24px; display:flex; align-items:center; gap:12px; color:#a5d6a7; }
        .version-banner ha-icon { color:#4caf50; }
        .version-banner a { color:#81c784; font-weight:500; }
        .warning ha-icon { color:#ff9800; --mdc-icon-size:24px; }
        .warning-text { flex:1; }
        .warning-title { color:#ff9800; font-weight:500; }
        .warning-sub { font-size:12px; color:#ccc; margin-top:4px; }
        
        /* Modal */
        .modal-bg { position:fixed; inset:0; background:rgba(0,0,0,0.7); display:flex; align-items:center; justify-content:center; z-index:1000; }
        .modal { background:#1a1a2e; border:1px solid #2a2a4a; border-radius:12px; padding:20px; width:90%; max-width:450px; }
        .modal-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid #2a2a4a; }
        .modal-head h3 { margin:0; font-size:18px; }
        .modal-close { background:none; border:none; color:#888; font-size:24px; cursor:pointer; }
        .modal-close:hover { color:#fff; }
        
        /* Form */
        .fg { margin-bottom:16px; }
        .fl { display:block; margin-bottom:6px; font-size:13px; color:#888; }
        .fi { width:100%; padding:10px 12px; border:1px solid #2a2a4a; border-radius:8px; background:#252545; color:#e8e8e8; font-size:14px; }
        .fi:focus { outline:none; border-color:#03a9f4; }
        select.fi { cursor:pointer; }
        
        /* HA Blaster badge */
        .ha-badge { display:inline-block; background:#1b3d1b; color:#4caf50; padding:2px 8px; border-radius:4px; font-size:10px; margin-top:8px; }
        
        /* Spinner animation */
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        
        /* Small buttons */
        .btn-sm { padding:4px 8px; font-size:11px; }
        .btn-sm ha-icon { --mdc-icon-size:14px; }
        
        /* Modal content area */
        .modal-content { background:#1a1a2e; border:1px solid #2a2a4a; border-radius:12px; padding:20px; width:90%; max-width:450px; }
        
        /* Success/Error colors */
        .success { color:#4caf50; }
        .error { color:#f44336; }
      </style>
      
      <div class="app">
        <aside class="sidebar">
          <div class="logo">
            <ha-icon icon="mdi:remote-tv"></ha-icon>
            <div class="logo-text">
              <span class="logo-title">OmniRemote Manager</span>
              <span class="logo-version">v${this._version}</span>
            </div>
          </div>
          <nav class="nav">
            <div class="nav-item ${this._view === 'dashboard' ? 'active' : ''}" data-nav="dashboard">
              <ha-icon icon="mdi:view-dashboard"></ha-icon>Dashboard
            </div>
            <div class="nav-item ${this._view === 'devices' ? 'active' : ''}" data-nav="devices">
              <ha-icon icon="mdi:devices"></ha-icon>Devices
              <span class="badge">${this._data.devices.length}</span>
            </div>
            <div class="nav-item ${this._view === 'scenes' ? 'active' : ''}" data-nav="scenes">
              <ha-icon icon="mdi:play-box-multiple"></ha-icon>Scenes
              <span class="badge">${this._data.scenes.length}</span>
            </div>
            <div class="nav-item ${this._view === 'blasters' ? 'active' : ''}" data-nav="blasters">
              <ha-icon icon="mdi:access-point"></ha-icon>Blasters
              <span class="badge">${this._data.blasters.length + this._data.haBlasters.length}</span>
            </div>
            <div class="nav-item ${this._view === 'catalog' ? 'active' : ''}" data-nav="catalog">
              <ha-icon icon="mdi:book-open-variant"></ha-icon>Catalog
            </div>
            
            <div class="nav-section">Rooms</div>
            ${this._data.rooms.map(r => `
              <div class="nav-item ${this._view === 'room' && this._roomId === r.id ? 'active' : ''}" data-nav="room" data-room="${r.id}">
                <ha-icon icon="${r.icon || 'mdi:sofa'}"></ha-icon>${r.name}
              </div>
            `).join('')}
            <div class="nav-item add-room" data-action="show-add-room">
              <ha-icon icon="mdi:plus"></ha-icon>Add Room
            </div>
          </nav>
        </aside>
        
        <main class="main">
          <header class="header">
            <h2>${this._getTitle()}</h2>
            <div>${this._getHeaderButtons()}</div>
          </header>
          ${this._versionMismatch ? `
            <div class="version-banner">
              <ha-icon icon="mdi:update"></ha-icon>
              <span>A new version (${this._versionMismatch}) is available. Please <a href="#" onclick="location.reload(); return false;">reload the page</a> or clear your browser cache.</span>
            </div>
          ` : ''}
          <div class="content">${this._getContent()}</div>
        </main>
      </div>
      
      ${this._modal ? `
        <div class="modal-bg" data-action="close-modal">
          <div class="modal" data-stop-propagation>
            ${this._modal}
          </div>
        </div>
      ` : ''}
    `;
    
    this._attachEvents();
  }

  _attachEvents() {
    const root = this.shadowRoot;
    
    // Navigation
    root.querySelectorAll('[data-nav]').forEach(el => {
      el.addEventListener('click', () => {
        this._view = el.dataset.nav;
        if (el.dataset.room) this._roomId = el.dataset.room;
        if (el.dataset.device) this._deviceId = el.dataset.device;
        this._render();
      });
    });
    
    // Actions - using event delegation on buttons
    root.querySelectorAll('[data-action]').forEach(el => {
      el.addEventListener('click', (e) => {
        // Don't close modal if clicking inside it
        if (el.dataset.action === 'close-modal' && e.target !== el) return;
        
        this._handleAction(el.dataset.action, el.dataset);
      });
    });
    
    // Stop modal propagation
    const modal = root.querySelector('[data-stop-propagation]');
    if (modal) {
      modal.addEventListener('click', (e) => e.stopPropagation());
    }
    
    // Dynamic dropdown handlers for action editor
    const deviceSelect = root.getElementById('action-device');
    if (deviceSelect) {
      deviceSelect.addEventListener('change', () => this._onDeviceChange());
    }
    
    const entitySelect = root.getElementById('action-entity');
    if (entitySelect) {
      entitySelect.addEventListener('change', () => this._onEntityChange());
    }
    
    const actionTypeSelect = root.getElementById('action-type');
    if (actionTypeSelect) {
      actionTypeSelect.addEventListener('change', () => this._updateActionTypeUI());
    }
    
    // Catalog filter handlers
    if (this._view === 'catalog') {
      this._setupCatalogFilters();
    }
  }

  async _handleAction(action, data) {
    console.log('[OmniRemote] Action:', action, data);
    
    switch (action) {
      case 'show-add-room':
        this._showAddRoomModal();
        break;
      case 'save-room':
        await this._saveRoom();
        break;
      case 'show-add-device':
        this._showAddDeviceModal();
        break;
      case 'save-device':
        await this._saveDevice();
        break;
      case 'show-add-scene':
        this._showSceneEditor();
        break;
      case 'edit-scene':
        this._showSceneEditor(data.sceneId);
        break;
      case 'save-scene':
        await this._saveScene();
        break;
      case 'activate-scene':
        await this._activateScene(data.sceneId);
        break;
      case 'deactivate-scene':
        await this._deactivateScene(data.sceneId);
        break;
      case 'discover':
        await this._discover();
        break;
      case 'discover-mdns':
        await this._discoverMdns();
        break;
      case 'show-add-blaster':
        this._showAddBlasterModal();
        break;
      case 'save-blaster':
        await this._saveBlaster();
        break;
      case 'close-modal':
        this._modal = null;
        this._render();
        break;
      case 'run-scene':
        await this._runScene(data.sceneId);
        break;
      case 'delete-scene':
        await this._deleteScene(data.sceneId);
        break;
      case 'add-on-action':
        this._showActionEditor('on');
        break;
      case 'add-off-action':
        this._showActionEditor('off');
        break;
      case 'edit-action':
        this._showActionEditor(data.type, parseInt(data.idx));
        break;
      case 'remove-action':
        this._removeAction(data.type, parseInt(data.idx));
        break;
      case 'cancel-action-edit':
        this._showSceneEditor(this._editingScene?.id, true);  // preserveState=true
        break;
      case 'save-action':
        this._saveAction();
        break;
      case 'save-scene-full':
        await this._saveSceneFull(data.sceneId);
        break;
      case 'add-catalog':
        await this._addFromCatalog(data.catalogId);
        break;
      case 'preview-catalog':
        this._showCatalogPreview(data.catalogId);
        break;
      case 'open-device':
        this._view = 'device';
        this._deviceId = data.deviceId;
        this._render();
        break;
      case 'send-cmd':
        this._sendCommand(data.deviceId, data.cmd);
        break;
      case 'test-cmd':
        this._testCommand(data.deviceId, data.cmd);
        break;
      case 'show-switch-profile':
        this._showSwitchProfileModal(data.deviceId, data.brand);
        break;
      case 'switch-profile':
        this._switchProfile(data.deviceId, data.profileId);
        break;
      case 'test-catalog-cmd':
        this._testCatalogCommand(data.profileId, data.cmd);
        break;
      case 'learn-code':
        this._showLearnCodeModal(data.deviceId);
        break;
    }
  }

  _setupCatalogFilters() {
    const search = this.shadowRoot.getElementById('catalog-search');
    const category = this.shadowRoot.getElementById('catalog-category');
    const brand = this.shadowRoot.getElementById('catalog-brand');
    
    if (search) {
      search.addEventListener('input', () => {
        this._catalogFilter = this._catalogFilter || {};
        this._catalogFilter.search = search.value;
        this._render();
      });
    }
    if (category) {
      category.addEventListener('change', () => {
        this._catalogFilter = this._catalogFilter || {};
        this._catalogFilter.category = category.value;
        this._render();
      });
    }
    if (brand) {
      brand.addEventListener('change', () => {
        this._catalogFilter = this._catalogFilter || {};
        this._catalogFilter.brand = brand.value;
        this._render();
      });
    }
  }

  _showCatalogPreview(catalogId) {
    const device = this._data.catalog.find(d => d.id === catalogId);
    if (!device) return;
    
    const commands = device.commands || device.ir_codes || {};
    const cmdList = Object.keys(commands);
    
    this._modal = `
      <div class="modal-head">
        <h3>${device.name}</h3>
        <button class="modal-close" data-action="close-modal">&times;</button>
      </div>
      <p style="color:#888;margin-top:0;">${device.brand} • ${device.category} ${device.model_years ? '• ' + device.model_years : ''}</p>
      ${device.description ? `<p style="font-size:13px;margin-bottom:16px;">${device.description}</p>` : ''}
      <h4>Commands (${cmdList.length}) - Click to test before adding</h4>
      <div style="max-height:300px;overflow-y:auto;border:1px solid var(--divider-color);border-radius:4px;padding:8px;">
        ${cmdList.map(cmd => {
          const c = commands[cmd];
          return `<div style="padding:4px 8px;border-bottom:1px solid var(--divider-color);display:flex;justify-content:space-between;align-items:center;">
            <span><strong>${cmd}</strong></span>
            <div style="display:flex;gap:8px;align-items:center;">
              <span style="color:#888;font-size:12px;">${c.type || c.protocol || 'ir'}</span>
              <button class="btn btn-s btn-sm" data-action="test-catalog-cmd" data-profile-id="${device.id}" data-cmd="${cmd}">Test</button>
            </div>
          </div>`;
        }).join('')}
      </div>
      <div style="margin-top:16px;display:flex;gap:8px;">
        <button class="btn btn-p" data-action="add-catalog" data-catalog-id="${device.id}"><ha-icon icon="mdi:plus"></ha-icon>Add Device</button>
        <button class="btn btn-s" data-action="close-modal">Close</button>
      </div>
    `;
    this._render();
  }

  _getTitle() {
    const titles = {
      dashboard: 'Dashboard',
      devices: 'All Devices',
      scenes: 'Scenes',
      blasters: 'Blasters',
      catalog: 'Device Catalog',
      room: this._data.rooms.find(r => r.id === this._roomId)?.name || 'Room',
      device: this._data.devices.find(d => d.id === this._deviceId)?.name || 'Device',
    };
    return titles[this._view] || 'Dashboard';
  }

  _getHeaderButtons() {
    switch (this._view) {
      case 'devices':
        return `<button class="btn btn-p" data-action="show-add-device"><ha-icon icon="mdi:plus"></ha-icon>Add Device</button>`;
      case 'scenes':
        return `<button class="btn btn-p" data-action="show-add-scene"><ha-icon icon="mdi:plus"></ha-icon>Add Scene</button>`;
      case 'blasters':
        return `
          <button class="btn btn-p" data-action="discover"><ha-icon icon="mdi:magnify"></ha-icon>Discover</button>
          <button class="btn btn-s" data-action="discover-mdns" style="margin-left:8px;"><ha-icon icon="mdi:access-point-network"></ha-icon>mDNS</button>
          <button class="btn btn-s" data-action="show-add-blaster" style="margin-left:8px;"><ha-icon icon="mdi:plus"></ha-icon>Add by IP</button>
        `;
      default:
        return '';
    }
  }

  _getContent() {
    switch (this._view) {
      case 'dashboard': return this._dashboardView();
      case 'devices': return this._devicesView();
      case 'scenes': return this._scenesView();
      case 'blasters': return this._blastersView();
      case 'catalog': return this._catalogView();
      case 'room': return this._roomView();
      case 'device': return this._deviceView();
      default: return this._dashboardView();
    }
  }

  _dashboardView() {
    const warning = !this._data.dbOk ? `
      <div class="warning">
        <ha-icon icon="mdi:alert"></ha-icon>
        <div class="warning-text">
          <div class="warning-title">Integration Not Configured</div>
          <div class="warning-sub">Go to Settings → Devices & Services → Add Integration → OmniRemote</div>
        </div>
      </div>
    ` : '';
    
    return `
      ${warning}
      <div class="stats">
        <div class="stat"><div class="stat-val">${this._data.devices.length}</div><div class="stat-lbl">Devices</div></div>
        <div class="stat"><div class="stat-val">${this._data.rooms.length}</div><div class="stat-lbl">Rooms</div></div>
        <div class="stat"><div class="stat-val">${this._data.blasters.length + this._data.haBlasters.length}</div><div class="stat-lbl">Blasters</div></div>
        <div class="stat"><div class="stat-val">${this._data.scenes.length}</div><div class="stat-lbl">Scenes</div></div>
        <div class="stat" style="border-color:#03a9f4;"><div class="stat-val" style="font-size:18px;">v${this._version}</div><div class="stat-lbl">Version</div></div>
      </div>
      <h3 style="margin-bottom:16px;">Quick Actions</h3>
      <div class="grid">
        ${this._data.scenes.slice(0, 6).map(s => `
          <div class="card">
            <div class="card-head">
              <div class="card-icon"><ha-icon icon="${s.icon || 'mdi:play'}"></ha-icon></div>
              <div class="card-info">
                <div class="card-title">${s.name}</div>
                <div class="card-sub">${s.actions?.length || 0} actions</div>
              </div>
            </div>
            <div class="card-btns">
              <button class="btn btn-p" data-action="run-scene" data-scene-id="${s.id}"><ha-icon icon="mdi:play"></ha-icon>Run</button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  _devicesView() {
    if (!this._data.devices.length) {
      return `<div class="empty"><ha-icon icon="mdi:devices"></ha-icon><h3>No Devices</h3><p>Add your first device</p><button class="btn btn-p" data-action="show-add-device">Add Device</button></div>`;
    }
    return `<div class="grid">${this._data.devices.map(d => `
      <div class="card">
        <div class="card-head">
          <div class="card-icon"><ha-icon icon="${this._catIcon(d.category)}"></ha-icon></div>
          <div class="card-info">
            <div class="card-title">${d.name}</div>
            <div class="card-sub">${d.brand || ''} ${d.model || ''}</div>
          </div>
        </div>
        <div class="card-btns">
          <button class="btn btn-s" data-action="open-device" data-device-id="${d.id}">Control</button>
        </div>
      </div>
    `).join('')}</div>`;
  }

  _scenesView() {
    if (!this._data.scenes.length) {
      return `<div class="empty"><ha-icon icon="mdi:play-box-multiple"></ha-icon><h3>No Scenes</h3><p>Create scenes to control multiple devices with ON and OFF sequences</p><button class="btn btn-p" data-action="show-add-scene">Add Scene</button></div>`;
    }
    
    // Group scenes by room
    const byRoom = {};
    const noRoom = [];
    
    this._data.scenes.forEach(s => {
      if (s.room_id) {
        if (!byRoom[s.room_id]) byRoom[s.room_id] = [];
        byRoom[s.room_id].push(s);
      } else {
        noRoom.push(s);
      }
    });
    
    let html = '';
    
    // Scenes grouped by room
    for (const roomId of Object.keys(byRoom)) {
      const room = this._data.rooms.find(r => r.id === roomId);
      const roomName = room ? room.name : 'Unknown Room';
      
      html += `<h3 style="margin:16px 0 8px;color:var(--primary-text-color)">${roomName}</h3>`;
      html += `<div class="grid">${byRoom[roomId].map(s => this._sceneCard(s)).join('')}</div>`;
    }
    
    // Scenes without room
    if (noRoom.length) {
      html += `<h3 style="margin:16px 0 8px;color:var(--primary-text-color)">Unassigned</h3>`;
      html += `<div class="grid">${noRoom.map(s => this._sceneCard(s)).join('')}</div>`;
    }
    
    return html;
  }
  
  _sceneCard(s) {
    const onCount = s.on_actions?.length || s.actions?.length || 0;
    const offCount = s.off_actions?.length || 0;
    const isActive = s.is_active;
    const room = s.room_id ? this._data.rooms.find(r => r.id === s.room_id) : null;
    const blaster = s.blaster_id ? this._data.blasters.find(b => b.id === s.blaster_id) : null;
    
    return `
      <div class="card ${isActive ? 'card-active' : ''}">
        <div class="card-head">
          <div class="card-icon" style="${isActive ? 'background:var(--success-color);' : ''}">
            <ha-icon icon="${s.icon || 'mdi:play'}"></ha-icon>
          </div>
          <div class="card-info">
            <div class="card-title">${s.name}</div>
            <div class="card-sub">
              ${onCount} ON / ${offCount} OFF actions
              ${blaster ? ` • ${blaster.name}` : ''}
            </div>
          </div>
        </div>
        <div class="card-btns">
          ${isActive 
            ? `<button class="btn" style="background:var(--error-color);color:white;" data-action="deactivate-scene" data-scene-id="${s.id}"><ha-icon icon="mdi:stop"></ha-icon>OFF</button>`
            : `<button class="btn btn-p" data-action="activate-scene" data-scene-id="${s.id}"><ha-icon icon="mdi:play"></ha-icon>ON</button>`
          }
          <button class="btn btn-s" data-action="edit-scene" data-scene-id="${s.id}"><ha-icon icon="mdi:pencil"></ha-icon></button>
          <button class="btn btn-d" data-action="delete-scene" data-scene-id="${s.id}"><ha-icon icon="mdi:delete"></ha-icon></button>
        </div>
      </div>
    `;
  }

  _blastersView() {
    const all = [...this._data.blasters, ...this._data.haBlasters];
    if (!all.length) {
      return `
        <div class="empty">
          <ha-icon icon="mdi:access-point"></ha-icon>
          <h3>No Blasters Found</h3>
          <p>Click Discover to find Broadlink devices, or add one manually by IP address</p>
          <button class="btn btn-p" data-action="discover" style="margin-right:8px;"><ha-icon icon="mdi:magnify"></ha-icon>Discover</button>
          <button class="btn btn-s" data-action="discover-mdns" style="margin-right:8px;"><ha-icon icon="mdi:access-point-network"></ha-icon>mDNS</button>
          <button class="btn btn-s" data-action="show-add-blaster"><ha-icon icon="mdi:plus"></ha-icon>Add by IP</button>
        </div>
      `;
    }
    return `<div class="grid">
      ${this._data.blasters.map(b => `
        <div class="card">
          <div class="card-head">
            <div class="card-icon"><ha-icon icon="mdi:access-point"></ha-icon></div>
            <div class="card-info">
              <div class="card-title">${b.name}</div>
              <div class="card-sub">${b.host} • ${b.mac}</div>
            </div>
          </div>
        </div>
      `).join('')}
      ${this._data.haBlasters.map(b => `
        <div class="card" style="border-color:#4caf50;">
          <div class="card-head">
            <div class="card-icon" style="background:#1b3d1b;"><ha-icon icon="mdi:home-assistant" style="color:#4caf50;"></ha-icon></div>
            <div class="card-info">
              <div class="card-title">${b.name}</div>
              <div class="card-sub">${b.entity_id}</div>
            </div>
          </div>
          <div class="ha-badge">From HA Broadlink Integration</div>
        </div>
      `).join('')}
    </div>`;
  }

  _catalogView() {
    const catalog = this._data.catalog || [];
    const categories = [...new Set(catalog.map(d => d.category))].sort();
    const brands = [...new Set(catalog.map(d => d.brand))].sort();
    
    // Filter by selected category/brand
    let filtered = catalog;
    if (this._catalogFilter?.category) {
      filtered = filtered.filter(d => d.category === this._catalogFilter.category);
    }
    if (this._catalogFilter?.brand) {
      filtered = filtered.filter(d => d.brand === this._catalogFilter.brand);
    }
    if (this._catalogFilter?.search) {
      const s = this._catalogFilter.search.toLowerCase();
      filtered = filtered.filter(d => 
        d.name.toLowerCase().includes(s) || 
        d.brand.toLowerCase().includes(s) ||
        (d.description || '').toLowerCase().includes(s)
      );
    }
    
    return `
      <div class="catalog-filters" style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;">
        <input type="text" class="fi" id="catalog-search" placeholder="Search devices..." 
               value="${this._catalogFilter?.search || ''}" style="max-width:200px;">
        <select class="fi" id="catalog-category" style="max-width:150px;">
          <option value="">All Categories</option>
          ${categories.map(c => `<option value="${c}" ${this._catalogFilter?.category === c ? 'selected' : ''}>${c}</option>`).join('')}
        </select>
        <select class="fi" id="catalog-brand" style="max-width:150px;">
          <option value="">All Brands</option>
          ${brands.map(b => `<option value="${b}" ${this._catalogFilter?.brand === b ? 'selected' : ''}>${b}</option>`).join('')}
        </select>
        <span style="color:#888;align-self:center;">${filtered.length} devices</span>
      </div>
      <div class="grid">${filtered.map(d => `
        <div class="card">
          <div class="card-head">
            <div class="card-icon"><ha-icon icon="${this._catIcon(d.category)}"></ha-icon></div>
            <div class="card-info">
              <div class="card-title">${d.name}</div>
              <div class="card-sub">${d.brand} • ${Object.keys(d.commands || d.ir_codes || {}).length} cmds</div>
              ${d.model_years ? `<div class="card-sub">${d.model_years}</div>` : ''}
            </div>
          </div>
          ${d.description ? `<p style="font-size:12px;color:#888;margin:8px 0;">${d.description}</p>` : ''}
          <div class="card-btns">
            <button class="btn btn-s" data-action="preview-catalog" data-catalog-id="${d.id}">Preview</button>
            <button class="btn btn-p" data-action="add-catalog" data-catalog-id="${d.id}"><ha-icon icon="mdi:plus"></ha-icon>Add</button>
          </div>
        </div>
      `).join('')}</div>
    `;
  }

  _roomView() {
    const room = this._data.rooms.find(r => r.id === this._roomId);
    const devices = this._data.devices.filter(d => d.room_id === this._roomId);
    if (!devices.length) {
      return `<div class="empty"><ha-icon icon="mdi:sofa"></ha-icon><h3>No Devices in ${room?.name || 'Room'}</h3><p>Add devices to this room</p></div>`;
    }
    return `<div class="grid">${devices.map(d => `
      <div class="card">
        <div class="card-head">
          <div class="card-icon"><ha-icon icon="${this._catIcon(d.category)}"></ha-icon></div>
          <div class="card-info"><div class="card-title">${d.name}</div></div>
        </div>
        <div class="card-btns">
          <button class="btn btn-s" data-action="open-device" data-device-id="${d.id}">Control</button>
        </div>
      </div>
    `).join('')}</div>`;
  }

  _deviceView() {
    const device = this._data.devices.find(d => d.id === this._deviceId);
    if (!device) return '<p>Device not found</p>';
    const cmds = Object.keys(device.commands || {});
    const catalogId = device.catalog_id || '';
    
    return `
      <div class="card" style="max-width:800px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
          <div>
            <h3 style="margin-top:0;">${device.name}</h3>
            <p style="color:#888;">${device.brand || ''} ${device.model || ''}</p>
            ${catalogId ? `<p style="color:#666;font-size:12px;">Profile: ${catalogId}</p>` : ''}
          </div>
          <div style="display:flex;gap:8px;">
            ${catalogId ? `<button class="btn btn-s" data-action="show-switch-profile" data-device-id="${device.id}" data-brand="${device.brand || ''}"><ha-icon icon="mdi:swap-horizontal"></ha-icon>Switch Profile</button>` : ''}
            <button class="btn btn-s" data-action="learn-code" data-device-id="${device.id}"><ha-icon icon="mdi:record"></ha-icon>Learn Code</button>
          </div>
        </div>
        
        <h4>Commands (${cmds.length})</h4>
        <div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(200px, 1fr));gap:8px;">
          ${cmds.map(c => {
            const code = device.commands[c];
            const protocol = code?.protocol || '';
            return `
              <div style="display:flex;gap:4px;align-items:center;background:var(--card-background-color);padding:8px;border-radius:4px;border:1px solid var(--divider-color);">
                <button class="btn btn-s" style="flex:1;" data-action="send-cmd" data-device-id="${device.id}" data-cmd="${c}">${c}</button>
                <button class="btn btn-d btn-sm" data-action="test-cmd" data-device-id="${device.id}" data-cmd="${c}" title="Test (with debug)"><ha-icon icon="mdi:play-circle-outline"></ha-icon></button>
              </div>
            `;
          }).join('')}
        </div>
        
        <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--divider-color);">
          <details>
            <summary style="cursor:pointer;color:#888;">Debug Info</summary>
            <pre style="font-size:11px;overflow-x:auto;background:#1a1a1a;padding:8px;border-radius:4px;">${JSON.stringify(device, null, 2)}</pre>
          </details>
        </div>
      </div>
    `;
  }

  _catIcon(cat) {
    const icons = {
      tv: 'mdi:television',
      projector: 'mdi:projector',
      receiver: 'mdi:speaker',
      soundbar: 'mdi:soundbar',
      streaming: 'mdi:cast',
      streamer: 'mdi:cast',
      cable_box: 'mdi:set-top-box',
      cable: 'mdi:set-top-box',
      ac: 'mdi:air-conditioner',
      fan: 'mdi:fan',
      light: 'mdi:lightbulb',
      lighting: 'mdi:lightbulb',
      bluray: 'mdi:disc-player',
      game_console: 'mdi:gamepad-variant',
      garage: 'mdi:garage',
      dvr: 'mdi:record-rec',
    };
    return icons[cat] || 'mdi:remote';
  }

  // === MODALS ===

  _showAddRoomModal() {
    this._modal = `
      <div class="modal-head">
        <h3>Add Room</h3>
        <button class="modal-close" data-action="close-modal">&times;</button>
      </div>
      <div class="fg">
        <label class="fl">Room Name</label>
        <input type="text" class="fi" id="room-name" placeholder="Living Room" autofocus>
      </div>
      <div class="fg">
        <label class="fl">Icon</label>
        <input type="text" class="fi" id="room-icon" value="mdi:sofa">
      </div>
      <button class="btn btn-p" data-action="save-room">Save Room</button>
    `;
    this._render();
  }

  _showAddDeviceModal() {
    this._modal = `
      <div class="modal-head">
        <h3>Add Device</h3>
        <button class="modal-close" data-action="close-modal">&times;</button>
      </div>
      <div class="fg">
        <label class="fl">Device Name</label>
        <input type="text" class="fi" id="device-name" placeholder="Samsung TV">
      </div>
      <div class="fg">
        <label class="fl">Category</label>
        <select class="fi" id="device-category">
          <option value="tv">TV</option>
          <option value="receiver">Receiver</option>
          <option value="soundbar">Soundbar</option>
          <option value="streaming">Streaming</option>
          <option value="projector">Projector</option>
          <option value="fan">Fan</option>
          <option value="ac">AC</option>
          <option value="light">Light</option>
          <option value="other">Other</option>
        </select>
      </div>
      <div class="fg">
        <label class="fl">Room</label>
        <select class="fi" id="device-room">
          <option value="">None</option>
          ${this._data.rooms.map(r => `<option value="${r.id}">${r.name}</option>`).join('')}
        </select>
      </div>
      <div class="fg">
        <label class="fl">Brand</label>
        <input type="text" class="fi" id="device-brand" placeholder="Samsung">
      </div>
      <button class="btn btn-p" data-action="save-device">Save Device</button>
    `;
    this._render();
  }

  _showAddSceneModal() {
    this._modal = `
      <div class="modal-head">
        <h3>Add Scene</h3>
        <button class="modal-close" data-action="close-modal">&times;</button>
      </div>
      <div class="fg">
        <label class="fl">Scene Name</label>
        <input type="text" class="fi" id="scene-name" placeholder="Watch TV">
      </div>
      <div class="fg">
        <label class="fl">Icon</label>
        <input type="text" class="fi" id="scene-icon" value="mdi:play">
      </div>
      <button class="btn btn-p" data-action="save-scene">Save Scene</button>
    `;
    this._render();
  }

  _showAddBlasterModal() {
    this._modal = `
      <div class="modal-head">
        <h3>Add Blaster by IP</h3>
        <button class="modal-close" data-action="close-modal">&times;</button>
      </div>
      <div class="fg">
        <label class="fl">IP Address</label>
        <input type="text" class="fi" id="blaster-ip" placeholder="192.168.1.100">
      </div>
      <div class="fg">
        <label class="fl">Name (optional)</label>
        <input type="text" class="fi" id="blaster-name" placeholder="Living Room Blaster">
      </div>
      <p style="color:#888;font-size:12px;">Find the IP in your Broadlink app or router's device list.</p>
      <button class="btn btn-p" data-action="save-blaster">Connect</button>
    `;
    this._render();
  }

  // === SAVE ACTIONS ===

  async _saveRoom() {
    const name = this.shadowRoot.getElementById('room-name')?.value?.trim();
    const icon = this.shadowRoot.getElementById('room-icon')?.value?.trim() || 'mdi:sofa';
    
    console.log('[OmniRemote] Saving room:', name, icon);
    
    if (!name) {
      alert('Please enter a room name');
      return;
    }
    
    const res = await this._api('/api/omniremote/rooms', 'POST', { name, icon });
    
    if (res.error) {
      alert('Error: ' + res.error);
    } else {
      this._modal = null;
      await this._loadData();
    }
  }

  async _saveDevice() {
    const name = this.shadowRoot.getElementById('device-name')?.value?.trim();
    const category = this.shadowRoot.getElementById('device-category')?.value;
    const room_id = this.shadowRoot.getElementById('device-room')?.value || null;
    const brand = this.shadowRoot.getElementById('device-brand')?.value?.trim() || '';
    
    console.log('[OmniRemote] Saving device:', { name, category, room_id, brand });
    
    if (!name) {
      alert('Please enter a device name');
      return;
    }
    
    const res = await this._api('/api/omniremote/devices', 'POST', { name, category, room_id, brand });
    
    if (res.error) {
      alert('Error: ' + res.error);
    } else {
      this._modal = null;
      await this._loadData();
    }
  }

  async _saveScene() {
    const name = this.shadowRoot.getElementById('scene-name')?.value?.trim();
    const icon = this.shadowRoot.getElementById('scene-icon')?.value?.trim() || 'mdi:play';
    
    if (!name) {
      alert('Please enter a scene name');
      return;
    }
    
    const res = await this._api('/api/omniremote/scenes', 'POST', { name, icon, actions: [] });
    
    if (res.error) {
      alert('Error: ' + res.error);
    } else {
      this._modal = null;
      await this._loadData();
    }
  }

  async _saveBlaster() {
    const host = this.shadowRoot.getElementById('blaster-ip')?.value?.trim();
    const name = this.shadowRoot.getElementById('blaster-name')?.value?.trim();
    
    console.log('[OmniRemote] Adding blaster:', host, name);
    
    if (!host) {
      alert('Please enter an IP address');
      return;
    }
    
    const res = await this._api('/api/omniremote/blasters', 'POST', { action: 'add', host, name });
    
    if (res.success) {
      this._modal = null;
      await this._loadData();
    } else {
      alert('Failed: ' + (res.error || 'Unknown error'));
    }
  }

  async _discover() {
    console.log('[OmniRemote] Starting discovery...');
    
    // Update button
    const btn = this.shadowRoot.querySelector('[data-action="discover"]');
    if (btn) btn.innerHTML = '<ha-icon icon="mdi:loading"></ha-icon>Discovering...';
    
    const res = await this._api('/api/omniremote/blasters', 'POST', {});
    
    console.log('[OmniRemote] Discovery result:', res);
    
    if (res.error) {
      alert('Discovery error: ' + res.error);
    } else {
      const count = res.discovered_count || res.blasters?.length || 0;
      if (count === 0) {
        alert('No Broadlink devices found.\n\nTips:\n• Broadcast discovery only works on same subnet\n• Try "mDNS" for cross-VLAN discovery\n• Try "Add by IP" with device\'s IP address');
      } else {
        alert(`Found ${count} device(s)!`);
      }
    }
    
    await this._loadData();
  }

  async _discoverMdns() {
    console.log('[OmniRemote] Starting mDNS discovery...');
    
    // Update button
    const btn = this.shadowRoot.querySelector('[data-action="discover-mdns"]');
    if (btn) btn.innerHTML = '<ha-icon icon="mdi:loading"></ha-icon>Scanning...';
    
    const res = await this._api('/api/omniremote/blasters', 'POST', { action: 'mdns' });
    
    console.log('[OmniRemote] mDNS discovery result:', res);
    
    if (res.error) {
      alert('mDNS discovery error: ' + res.error);
    } else {
      const count = res.discovered_count || res.blasters?.length || 0;
      if (count === 0) {
        alert('No Broadlink devices found via mDNS.\n\nTips:\n• mDNS must be relayed across VLANs (Avahi/mDNS reflector)\n• Device must be advertising on _broadlink._tcp\n• Try "Add by IP" with device\'s IP address');
      } else {
        alert(`Found ${count} device(s) via mDNS!`);
      }
    }
    
    // Reset button
    if (btn) btn.innerHTML = '<ha-icon icon="mdi:access-point-network"></ha-icon>mDNS';
    
    await this._loadData();
  }

  async _runScene(id) {
    console.log('[OmniRemote] Running scene:', id);
    await this._activateScene(id);
  }

  async _activateScene(id) {
    console.log('[OmniRemote] Activating scene:', id);
    const res = await this._api('/api/omniremote/scenes', 'POST', { action: 'activate', scene_id: id });
    if (res.error) {
      alert('Error activating scene: ' + res.error);
    }
    await this._loadData();
  }

  async _deactivateScene(id) {
    console.log('[OmniRemote] Deactivating scene:', id);
    const res = await this._api('/api/omniremote/scenes', 'POST', { action: 'deactivate', scene_id: id });
    if (res.error) {
      alert('Error deactivating scene: ' + res.error);
    }
    await this._loadData();
  }

  async _deleteScene(id) {
    if (!confirm('Delete this scene? This cannot be undone.')) return;
    await this._api('/api/omniremote/scenes', 'DELETE', { id });
    await this._loadData();
  }

  _showSceneEditor(sceneId = null, preserveState = false) {
    // If preserveState is true and we already have an editing scene, keep it
    // This is used when returning from the action editor
    if (preserveState && this._editingScene) {
      // Just re-render with current state
    } else {
      // Load from saved data or create new
      const scene = sceneId ? this._data.scenes.find(s => s.id === sceneId) : null;
      this._editingScene = scene ? JSON.parse(JSON.stringify(scene)) : {
        id: null,
        name: '',
        icon: 'mdi:television',
        room_id: null,
        blaster_id: null,
        controlled_device_ids: [],
        controlled_entity_ids: [],
        on_actions: [],
        off_actions: []
      };
    }
    
    const isEdit = !!this._editingScene.id || (sceneId && this._data.scenes.find(s => s.id === sceneId));
    
    this._modal = `
      <div class="modal-content" style="max-width:800px;max-height:90vh;overflow-y:auto;">
        <h3>${isEdit ? 'Edit' : 'Create'} Scene</h3>
        
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
          <div>
            <label class="fl">Scene Name</label>
            <input type="text" class="fi" id="scene-name" value="${this._editingScene.name}" placeholder="Watch TV">
          </div>
          <div>
            <label class="fl">Icon</label>
            <input type="text" class="fi" id="scene-icon" value="${this._editingScene.icon || 'mdi:television'}">
          </div>
        </div>
        
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
          <div>
            <label class="fl">Room</label>
            <select class="fi" id="scene-room">
              <option value="">-- No Room --</option>
              ${this._data.rooms.map(r => `<option value="${r.id}" ${this._editingScene.room_id === r.id ? 'selected' : ''}>${r.name}</option>`).join('')}
            </select>
          </div>
          <div>
            <label class="fl">Default Blaster</label>
            <select class="fi" id="scene-blaster">
              <option value="">-- Select Blaster --</option>
              ${this._data.blasters.map(b => `<option value="${b.id}" ${this._editingScene.blaster_id === b.id ? 'selected' : ''}>${b.name}</option>`).join('')}
            </select>
          </div>
        </div>
        
        <div style="display:flex;gap:16px;margin-bottom:16px;">
          <div style="flex:1;">
            <h4 style="margin:0 0 8px;display:flex;align-items:center;justify-content:space-between;">
              <span><ha-icon icon="mdi:play" style="color:var(--success-color);"></ha-icon> ON Sequence</span>
              <button class="btn btn-s btn-sm" data-action="add-on-action"><ha-icon icon="mdi:plus"></ha-icon>Add</button>
            </h4>
            <div id="on-actions-list" style="min-height:100px;border:1px solid var(--divider-color);border-radius:8px;padding:8px;">
              ${this._renderActionsList(this._editingScene.on_actions, 'on')}
            </div>
          </div>
          
          <div style="flex:1;">
            <h4 style="margin:0 0 8px;display:flex;align-items:center;justify-content:space-between;">
              <span><ha-icon icon="mdi:stop" style="color:var(--error-color);"></ha-icon> OFF Sequence</span>
              <button class="btn btn-s btn-sm" data-action="add-off-action"><ha-icon icon="mdi:plus"></ha-icon>Add</button>
            </h4>
            <div id="off-actions-list" style="min-height:100px;border:1px solid var(--divider-color);border-radius:8px;padding:8px;">
              ${this._renderActionsList(this._editingScene.off_actions, 'off')}
            </div>
          </div>
        </div>
        
        <div style="display:flex;gap:8px;justify-content:flex-end;">
          <button class="btn btn-s" data-action="close-modal">Cancel</button>
          <button class="btn btn-p" data-action="save-scene-full" data-scene-id="${sceneId || ''}">Save Scene</button>
        </div>
      </div>
    `;
    this._render();
  }

  _renderActionsList(actions, type) {
    if (!actions || !actions.length) {
      return `<div style="color:var(--secondary-text-color);text-align:center;padding:20px;">No actions yet. Click Add to create one.</div>`;
    }
    
    return actions.map((action, idx) => {
      let desc = '';
      let icon = 'mdi:help';
      
      switch (action.action_type) {
        case 'ir_command':
          const device = this._data.devices.find(d => d.id === action.device_id);
          desc = `IR: ${device?.name || action.device_id} → ${action.command_name || 'command'}`;
          icon = 'mdi:remote';
          break;
        case 'ha_service':
          desc = `HA: ${action.ha_service} on ${action.entity_id}`;
          icon = 'mdi:home-assistant';
          break;
        case 'network_command':
          desc = `Network: ${action.network_command}`;
          icon = 'mdi:lan';
          break;
        case 'delay':
          desc = `Delay: ${action.delay_seconds}s`;
          icon = 'mdi:timer-sand';
          break;
        default:
          desc = action.action_type;
      }
      
      return `
        <div class="action-item" style="display:flex;align-items:center;gap:8px;padding:8px;background:var(--card-background-color);border-radius:4px;margin-bottom:4px;">
          <ha-icon icon="${icon}" style="opacity:0.7;"></ha-icon>
          <span style="flex:1;font-size:13px;">${desc}</span>
          <span style="color:var(--secondary-text-color);font-size:11px;">+${action.delay_seconds || 0}s</span>
          <button class="btn btn-d btn-sm" data-action="edit-action" data-type="${type}" data-idx="${idx}"><ha-icon icon="mdi:pencil"></ha-icon></button>
          <button class="btn btn-d btn-sm" data-action="remove-action" data-type="${type}" data-idx="${idx}"><ha-icon icon="mdi:delete"></ha-icon></button>
        </div>
      `;
    }).join('');
  }

  _showActionEditor(type, idx = null) {
    // First, capture current form values into _editingScene
    // This preserves scene name, icon, etc. when navigating to action editor
    const nameInput = this.shadowRoot.getElementById('scene-name');
    const iconInput = this.shadowRoot.getElementById('scene-icon');
    const roomInput = this.shadowRoot.getElementById('scene-room');
    const blasterInput = this.shadowRoot.getElementById('scene-blaster');
    
    if (nameInput) this._editingScene.name = nameInput.value || '';
    if (iconInput) this._editingScene.icon = iconInput.value || 'mdi:television';
    if (roomInput) this._editingScene.room_id = roomInput.value || null;
    if (blasterInput) this._editingScene.blaster_id = blasterInput.value || null;
    
    const actions = type === 'on' ? this._editingScene.on_actions : this._editingScene.off_actions;
    const action = idx !== null ? actions[idx] : {
      action_type: 'ir_command',
      device_id: null,
      command_name: null,
      entity_id: null,
      ha_service: null,
      network_command: null,
      delay_seconds: 0.5,
      skip_if_on: type === 'on'
    };
    
    this._editingAction = { type, idx, action: JSON.parse(JSON.stringify(action)) };
    
    this._modal = `
      <div class="modal-content" style="max-width:500px;">
        <h3>${idx !== null ? 'Edit' : 'Add'} Action</h3>
        
        <label class="fl">Action Type</label>
        <select class="fi" id="action-type">
          <option value="ir_command" ${action.action_type === 'ir_command' ? 'selected' : ''}>IR/RF Command</option>
          <option value="ha_service" ${action.action_type === 'ha_service' ? 'selected' : ''}>Home Assistant Service</option>
          <option value="network_command" ${action.action_type === 'network_command' ? 'selected' : ''}>Network Device</option>
          <option value="delay" ${action.action_type === 'delay' ? 'selected' : ''}>Delay Only</option>
        </select>
        
        <div id="action-fields" style="margin-top:16px;">
          ${this._getActionFields(action)}
        </div>
        
        <div style="margin-top:16px;">
          <label class="fl">Delay After (seconds)</label>
          <input type="number" class="fi" id="action-delay" value="${action.delay_seconds || 0.5}" min="0" step="0.1">
        </div>
        
        ${type === 'on' ? `
          <div style="margin-top:12px;">
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
              <input type="checkbox" id="action-skip-if-on" ${action.skip_if_on ? 'checked' : ''}>
              Skip if device already on from another scene
            </label>
          </div>
        ` : ''}
        
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
          <button class="btn btn-s" data-action="cancel-action-edit">Cancel</button>
          <button class="btn btn-p" data-action="save-action">Save Action</button>
        </div>
      </div>
    `;
    this._render();
  }

  _getActionFields(action) {
    switch (action.action_type) {
      case 'ir_command':
        const selectedDevice = action.device_id ? this._data.devices.find(d => d.id === action.device_id) : null;
        // Commands are stored as a dict with command name as key
        const commands = selectedDevice?.commands ? Object.keys(selectedDevice.commands) : [];
        
        return `
          <label class="fl">Device</label>
          <select class="fi" id="action-device" onchange="this.getRootNode().host._onDeviceChange()">
            <option value="">-- Select Device --</option>
            ${this._data.devices.map(d => {
              const cmdCount = d.commands ? Object.keys(d.commands).length : 0;
              return `<option value="${d.id}" ${action.device_id === d.id ? 'selected' : ''}>${d.name} (${cmdCount} cmds)</option>`;
            }).join('')}
          </select>
          
          <label class="fl" style="margin-top:12px;">Command</label>
          <select class="fi" id="action-command">
            <option value="">-- Select Command --</option>
            ${commands.map(c => `<option value="${c}" ${action.command_name === c ? 'selected' : ''}>${c}</option>`).join('')}
          </select>
          ${commands.length === 0 && selectedDevice ? '<p style="color:var(--warning-color);font-size:12px;margin-top:4px;">⚠️ No commands found. Add commands in device editor first.</p>' : ''}
          ${!selectedDevice ? '<p style="color:var(--secondary-text-color);font-size:12px;margin-top:4px;">Select a device to see available commands.</p>' : ''}
        `;
        
      case 'ha_service':
        return this._getHaServiceFields(action);
        
      case 'network_command':
        return `
          <label class="fl">Network Device</label>
          <select class="fi" id="action-network-device">
            <option value="">-- Select Device --</option>
            ${(this._data.networkDevices || []).map(d => `<option value="${d.id}" ${action.network_device_id === d.id ? 'selected' : ''}>${d.name}</option>`).join('')}
          </select>
          
          <label class="fl" style="margin-top:12px;">Command</label>
          <input type="text" class="fi" id="action-network-cmd" value="${action.network_command || ''}" placeholder="e.g., power, home, select">
        `;
        
      case 'delay':
        return `<p style="color:var(--secondary-text-color);">This action only adds a delay. Set the delay time below.</p>`;
        
      default:
        return '';
    }
  }

  _getHaServiceFields(action) {
    const entities = this._data.haEntities || [];
    
    // Group entities by domain for better organization
    const groups = {
      'Media & Entertainment': entities.filter(e => ['media_player', 'remote'].includes(e.domain)),
      'Lighting': entities.filter(e => e.domain === 'light'),
      'Switches & Plugs': entities.filter(e => ['switch', 'input_boolean'].includes(e.domain)),
      'Climate & Comfort': entities.filter(e => ['climate', 'fan', 'humidifier'].includes(e.domain)),
      'Covers & Blinds': entities.filter(e => e.domain === 'cover'),
      'Scenes & Scripts': entities.filter(e => ['scene', 'script', 'automation'].includes(e.domain)),
      'Inputs': entities.filter(e => ['input_number', 'input_select'].includes(e.domain)),
      'Other': entities.filter(e => ['vacuum', 'lock', 'siren'].includes(e.domain)),
    };
    
    const selectedEntity = action.entity_id ? entities.find(e => e.entity_id === action.entity_id) : null;
    const domain = selectedEntity?.domain || '';
    
    // Build entity options with grouped dropdowns
    let entityOptions = '<option value="">-- Select Entity --</option>';
    for (const [groupName, groupEntities] of Object.entries(groups)) {
      if (groupEntities.length > 0) {
        entityOptions += `<optgroup label="${groupName}">`;
        entityOptions += groupEntities.map(e => 
          `<option value="${e.entity_id}" ${action.entity_id === e.entity_id ? 'selected' : ''}>${e.name}</option>`
        ).join('');
        entityOptions += '</optgroup>';
      }
    }
    
    // Get services for the selected domain
    const services = this._getServicesForDomain(domain, action.ha_service);
    
    return `
      <label class="fl">Entity</label>
      <select class="fi" id="action-entity" onchange="this.getRootNode().host._onEntityChange()">
        ${entityOptions}
      </select>
      
      <label class="fl" style="margin-top:12px;">Service</label>
      <select class="fi" id="action-service" onchange="this.getRootNode().host._onServiceChange()">
        ${services}
      </select>
      
      <div id="service-data-fields" style="margin-top:12px;">
        ${this._getServiceDataFields(action, selectedEntity)}
      </div>
    `;
  }

  _getServicesForDomain(domain, currentService) {
    const isSelected = (svc) => currentService?.includes(svc) ? 'selected' : '';
    
    // Base services available to most domains
    let services = `
      <option value="">-- Select Service --</option>
      <option value="turn_on" ${isSelected('turn_on')}>Turn On</option>
      <option value="turn_off" ${isSelected('turn_off')}>Turn Off</option>
      <option value="toggle" ${isSelected('toggle')}>Toggle</option>
    `;
    
    // Domain-specific services
    switch (domain) {
      case 'media_player':
        services += `
          <optgroup label="Input/Source">
            <option value="select_source" ${isSelected('select_source')}>Select Source/Input</option>
          </optgroup>
          <optgroup label="Volume">
            <option value="volume_set" ${isSelected('volume_set')}>Set Volume</option>
            <option value="volume_up" ${isSelected('volume_up')}>Volume Up</option>
            <option value="volume_down" ${isSelected('volume_down')}>Volume Down</option>
            <option value="volume_mute" ${isSelected('volume_mute')}>Mute/Unmute</option>
          </optgroup>
          <optgroup label="Playback">
            <option value="media_play" ${isSelected('media_play')}>Play</option>
            <option value="media_pause" ${isSelected('media_pause')}>Pause</option>
            <option value="media_play_pause" ${isSelected('media_play_pause')}>Play/Pause</option>
            <option value="media_stop" ${isSelected('media_stop')}>Stop</option>
            <option value="media_next_track" ${isSelected('media_next_track')}>Next Track</option>
            <option value="media_previous_track" ${isSelected('media_previous_track')}>Previous Track</option>
          </optgroup>
        `;
        break;
        
      case 'light':
        services += `
          <optgroup label="Brightness">
            <option value="brightness_set" ${isSelected('brightness_set')}>Set Brightness</option>
          </optgroup>
          <optgroup label="Color">
            <option value="color_temp_set" ${isSelected('color_temp_set')}>Set Color Temperature</option>
          </optgroup>
        `;
        break;
        
      case 'climate':
        services += `
          <optgroup label="Mode">
            <option value="set_hvac_mode" ${isSelected('set_hvac_mode')}>Set HVAC Mode</option>
            <option value="set_preset_mode" ${isSelected('set_preset_mode')}>Set Preset Mode</option>
          </optgroup>
          <optgroup label="Temperature">
            <option value="set_temperature" ${isSelected('set_temperature')}>Set Temperature</option>
          </optgroup>
        `;
        break;
        
      case 'cover':
        services += `
          <optgroup label="Position">
            <option value="open_cover" ${isSelected('open_cover')}>Open</option>
            <option value="close_cover" ${isSelected('close_cover')}>Close</option>
            <option value="stop_cover" ${isSelected('stop_cover')}>Stop</option>
            <option value="set_cover_position" ${isSelected('set_cover_position')}>Set Position</option>
          </optgroup>
        `;
        break;
        
      case 'fan':
        services += `
          <optgroup label="Speed">
            <option value="set_percentage" ${isSelected('set_percentage')}>Set Speed %</option>
            <option value="set_preset_mode" ${isSelected('set_preset_mode')}>Set Preset Mode</option>
          </optgroup>
        `;
        break;
        
      case 'scene':
        // Scenes only have turn_on
        services = `
          <option value="">-- Select Service --</option>
          <option value="turn_on" ${isSelected('turn_on')}>Activate Scene</option>
        `;
        break;
        
      case 'script':
        services = `
          <option value="">-- Select Service --</option>
          <option value="turn_on" ${isSelected('turn_on')}>Run Script</option>
          <option value="turn_off" ${isSelected('turn_off')}>Stop Script</option>
        `;
        break;
        
      case 'automation':
        services += `
          <option value="trigger" ${isSelected('trigger')}>Trigger</option>
        `;
        break;
        
      case 'input_number':
        services = `
          <option value="">-- Select Service --</option>
          <option value="set_value" ${isSelected('set_value')}>Set Value</option>
          <option value="increment" ${isSelected('increment')}>Increment</option>
          <option value="decrement" ${isSelected('decrement')}>Decrement</option>
        `;
        break;
        
      case 'input_select':
        services = `
          <option value="">-- Select Service --</option>
          <option value="select_option" ${isSelected('select_option')}>Select Option</option>
          <option value="select_next" ${isSelected('select_next')}>Next Option</option>
          <option value="select_previous" ${isSelected('select_previous')}>Previous Option</option>
        `;
        break;
        
      case 'lock':
        services = `
          <option value="">-- Select Service --</option>
          <option value="lock" ${isSelected('lock')}>Lock</option>
          <option value="unlock" ${isSelected('unlock')}>Unlock</option>
        `;
        break;
        
      case 'vacuum':
        services += `
          <option value="start" ${isSelected('start')}>Start</option>
          <option value="pause" ${isSelected('pause')}>Pause</option>
          <option value="stop" ${isSelected('stop')}>Stop</option>
          <option value="return_to_base" ${isSelected('return_to_base')}>Return to Base</option>
        `;
        break;
    }
    
    return services;
  }

  _getServiceDataFields(action, entity) {
    if (!action.ha_service) return '';
    
    const service = action.ha_service.split('.').pop();
    const serviceData = action.service_data || {};
    const domain = entity?.domain || '';
    
    switch (service) {
      case 'select_source':
        const sources = entity?.sources || [];
        return `
          <label class="fl">Source/Input</label>
          ${sources.length ? `
            <select class="fi" id="service-data-source">
              <option value="">-- Select Source --</option>
              ${sources.map(s => `<option value="${s}" ${serviceData.source === s ? 'selected' : ''}>${s}</option>`).join('')}
            </select>
          ` : `
            <input type="text" class="fi" id="service-data-source" value="${serviceData.source || ''}" placeholder="e.g., HDMI 1, TV, Roku">
          `}
        `;
        
      case 'volume_set':
        return `
          <label class="fl">Volume Level (0-1)</label>
          <input type="number" class="fi" id="service-data-volume" value="${serviceData.volume_level || 0.5}" min="0" max="1" step="0.05">
        `;
        
      case 'volume_mute':
        return `
          <label class="fl">Mute</label>
          <select class="fi" id="service-data-mute">
            <option value="true" ${serviceData.is_volume_muted === true ? 'selected' : ''}>Mute</option>
            <option value="false" ${serviceData.is_volume_muted === false ? 'selected' : ''}>Unmute</option>
          </select>
        `;
        
      case 'brightness_set':
        return `
          <label class="fl">Brightness (0-255)</label>
          <input type="number" class="fi" id="service-data-brightness" value="${serviceData.brightness || 255}" min="0" max="255" step="1">
        `;
        
      case 'set_temperature':
        return `
          <label class="fl">Temperature</label>
          <input type="number" class="fi" id="service-data-temperature" value="${serviceData.temperature || 72}" min="50" max="90" step="1">
        `;
        
      case 'set_hvac_mode':
        const hvacModes = entity?.hvac_modes || ['off', 'heat', 'cool', 'auto'];
        return `
          <label class="fl">HVAC Mode</label>
          <select class="fi" id="service-data-hvac-mode">
            ${hvacModes.map(m => `<option value="${m}" ${serviceData.hvac_mode === m ? 'selected' : ''}>${m}</option>`).join('')}
          </select>
        `;
        
      case 'set_preset_mode':
        const presetModes = entity?.preset_modes || [];
        return presetModes.length ? `
          <label class="fl">Preset Mode</label>
          <select class="fi" id="service-data-preset-mode">
            ${presetModes.map(m => `<option value="${m}" ${serviceData.preset_mode === m ? 'selected' : ''}>${m}</option>`).join('')}
          </select>
        ` : '';
        
      case 'set_cover_position':
        return `
          <label class="fl">Position (0-100)</label>
          <input type="number" class="fi" id="service-data-position" value="${serviceData.position || 50}" min="0" max="100" step="5">
        `;
        
      case 'set_percentage':
        return `
          <label class="fl">Speed % (0-100)</label>
          <input type="number" class="fi" id="service-data-percentage" value="${serviceData.percentage || 50}" min="0" max="100" step="10">
        `;
        
      case 'set_value':
        return `
          <label class="fl">Value</label>
          <input type="number" class="fi" id="service-data-value" value="${serviceData.value || 0}" step="any">
        `;
        
      case 'select_option':
        const options = entity?.options || [];
        return options.length ? `
          <label class="fl">Option</label>
          <select class="fi" id="service-data-option">
            ${options.map(o => `<option value="${o}" ${serviceData.option === o ? 'selected' : ''}>${o}</option>`).join('')}
          </select>
        ` : `
          <label class="fl">Option</label>
          <input type="text" class="fi" id="service-data-option" value="${serviceData.option || ''}" placeholder="Option name">
        `;
        
      default:
        return '';
    }
  }

  _onDeviceChange() {
    const deviceId = this.shadowRoot.getElementById('action-device')?.value;
    if (!deviceId) return;
    
    const device = this._data.devices.find(d => d.id === deviceId);
    if (!device) return;
    
    // Update command dropdown
    const commandSelect = this.shadowRoot.getElementById('action-command');
    if (commandSelect) {
      const commands = device.commands ? Object.keys(device.commands) : [];
      commandSelect.innerHTML = `
        <option value="">-- Select Command --</option>
        ${commands.map(c => `<option value="${c}">${c}</option>`).join('')}
      `;
    }
  }

  _onEntityChange() {
    const entityId = this.shadowRoot.getElementById('action-entity')?.value;
    if (!entityId) return;
    
    const entity = (this._data.haEntities || []).find(e => e.entity_id === entityId);
    const domain = entity?.domain || '';
    
    // Update service dropdown with relevant options for domain
    const serviceSelect = this.shadowRoot.getElementById('action-service');
    if (serviceSelect) {
      serviceSelect.innerHTML = this._getServicesForDomain(domain, '');
    }
    
    // Clear service data fields
    const serviceDataDiv = this.shadowRoot.getElementById('service-data-fields');
    if (serviceDataDiv) {
      serviceDataDiv.innerHTML = '';
    }
  }

  _onServiceChange() {
    const entityId = this.shadowRoot.getElementById('action-entity')?.value;
    const service = this.shadowRoot.getElementById('action-service')?.value;
    
    if (!service) return;
    
    const entity = (this._data.haEntities || []).find(e => e.entity_id === entityId);
    const domain = entity?.domain || '';
    
    // Update service data fields based on selected service
    const serviceDataDiv = this.shadowRoot.getElementById('service-data-fields');
    if (serviceDataDiv) {
      const action = {
        ha_service: `${domain}.${service}`,
        service_data: {}
      };
      serviceDataDiv.innerHTML = this._getServiceDataFields(action, entity);
    }
  }

  _updateActionTypeUI() {
    // Re-render the action fields when action type changes
    const actionType = this.shadowRoot.getElementById('action-type')?.value;
    if (!actionType) return;
    
    // Update the editing action with new type
    if (this._editingAction) {
      this._editingAction.action.action_type = actionType;
    }
    
    // Get the action fields container
    const fieldsDiv = this.shadowRoot.getElementById('action-fields');
    if (fieldsDiv) {
      fieldsDiv.innerHTML = this._getActionFields(this._editingAction?.action || { action_type: actionType });
      
      // Re-attach event listeners for new dropdowns
      const deviceSelect = this.shadowRoot.getElementById('action-device');
      if (deviceSelect) {
        deviceSelect.addEventListener('change', () => this._onDeviceChange());
      }
      
      const entitySelect = this.shadowRoot.getElementById('action-entity');
      if (entitySelect) {
        entitySelect.addEventListener('change', () => this._onEntityChange());
      }
    }
  }

  _removeAction(type, idx) {
    const actions = type === 'on' ? this._editingScene.on_actions : this._editingScene.off_actions;
    actions.splice(idx, 1);
    this._showSceneEditor(this._editingScene.id, true);  // preserveState=true
  }

  _saveAction() {
    const actionType = this.shadowRoot.getElementById('action-type')?.value;
    const delay = parseFloat(this.shadowRoot.getElementById('action-delay')?.value) || 0.5;
    const skipIfOn = this.shadowRoot.getElementById('action-skip-if-on')?.checked || false;
    
    const action = {
      id: this._editingAction?.action?.id || this._generateId(),
      order: this._editingAction?.idx ?? (this._editingAction?.type === 'on' ? this._editingScene.on_actions.length : this._editingScene.off_actions.length),
      action_type: actionType,
      delay_seconds: delay,
      skip_if_on: skipIfOn,
    };
    
    // Get type-specific fields
    switch (actionType) {
      case 'ir_command':
        action.device_id = this.shadowRoot.getElementById('action-device')?.value;
        action.command_name = this.shadowRoot.getElementById('action-command')?.value;
        break;
      case 'ha_service':
        action.entity_id = this.shadowRoot.getElementById('action-entity')?.value;
        const service = this.shadowRoot.getElementById('action-service')?.value;
        const domain = action.entity_id?.split('.')[0] || 'homeassistant';
        action.ha_service = `${domain}.${service}`;
        
        // Get service data based on service type
        action.service_data = {};
        
        // Source/Input
        const sourceInput = this.shadowRoot.getElementById('service-data-source');
        if (sourceInput?.value) action.service_data.source = sourceInput.value;
        
        // Volume
        const volumeInput = this.shadowRoot.getElementById('service-data-volume');
        if (volumeInput?.value) action.service_data.volume_level = parseFloat(volumeInput.value);
        
        // Mute
        const muteInput = this.shadowRoot.getElementById('service-data-mute');
        if (muteInput?.value) action.service_data.is_volume_muted = muteInput.value === 'true';
        
        // Brightness
        const brightnessInput = this.shadowRoot.getElementById('service-data-brightness');
        if (brightnessInput?.value) action.service_data.brightness = parseInt(brightnessInput.value);
        
        // Temperature
        const tempInput = this.shadowRoot.getElementById('service-data-temperature');
        if (tempInput?.value) action.service_data.temperature = parseFloat(tempInput.value);
        
        // HVAC Mode
        const hvacInput = this.shadowRoot.getElementById('service-data-hvac-mode');
        if (hvacInput?.value) action.service_data.hvac_mode = hvacInput.value;
        
        // Preset Mode
        const presetInput = this.shadowRoot.getElementById('service-data-preset-mode');
        if (presetInput?.value) action.service_data.preset_mode = presetInput.value;
        
        // Cover Position
        const positionInput = this.shadowRoot.getElementById('service-data-position');
        if (positionInput?.value) action.service_data.position = parseInt(positionInput.value);
        
        // Fan Percentage
        const percentageInput = this.shadowRoot.getElementById('service-data-percentage');
        if (percentageInput?.value) action.service_data.percentage = parseInt(percentageInput.value);
        
        // Input Number Value
        const valueInput = this.shadowRoot.getElementById('service-data-value');
        if (valueInput?.value) action.service_data.value = parseFloat(valueInput.value);
        
        // Input Select Option
        const optionInput = this.shadowRoot.getElementById('service-data-option');
        if (optionInput?.value) action.service_data.option = optionInput.value;
        
        break;
      case 'network_command':
        action.network_device_id = this.shadowRoot.getElementById('action-network-device')?.value;
        action.network_command = this.shadowRoot.getElementById('action-network-cmd')?.value;
        break;
    }
    
    // Add or update action
    const actions = this._editingAction.type === 'on' ? this._editingScene.on_actions : this._editingScene.off_actions;
    if (this._editingAction.idx !== null) {
      actions[this._editingAction.idx] = action;
    } else {
      actions.push(action);
    }
    
    // Return to scene editor, preserving our edited state
    this._showSceneEditor(this._editingScene.id, true);  // preserveState=true
  }

  async _saveSceneFull(sceneId) {
    const name = this.shadowRoot.getElementById('scene-name')?.value?.trim();
    const icon = this.shadowRoot.getElementById('scene-icon')?.value?.trim() || 'mdi:television';
    const roomId = this.shadowRoot.getElementById('scene-room')?.value || null;
    const blasterId = this.shadowRoot.getElementById('scene-blaster')?.value || null;
    
    if (!name) {
      alert('Please enter a scene name');
      return;
    }
    
    const sceneData = {
      name,
      icon,
      room_id: roomId,
      blaster_id: blasterId,
      on_actions: this._editingScene.on_actions,
      off_actions: this._editingScene.off_actions,
      controlled_device_ids: this._editingScene.on_actions
        .filter(a => a.action_type === 'ir_command' && a.device_id)
        .map(a => a.device_id),
      controlled_entity_ids: this._editingScene.on_actions
        .filter(a => a.action_type === 'ha_service' && a.entity_id)
        .map(a => a.entity_id),
    };
    
    let res;
    if (sceneId) {
      sceneData.id = sceneId;
      res = await this._api('/api/omniremote/scenes', 'PUT', sceneData);
    } else {
      res = await this._api('/api/omniremote/scenes', 'POST', sceneData);
    }
    
    if (res.error) {
      alert('Error saving scene: ' + res.error);
      return;
    }
    
    this._modal = null;
    this._editingScene = null;
    await this._loadData();
  }

  _generateId() {
    return Math.random().toString(36).substring(2, 10);
  }

  async _addFromCatalog(id) {
    const res = await this._api('/api/omniremote/catalog', 'POST', { catalog_id: id });
    if (res.device) {
      const msg = `Added: ${res.device.name}\nCommands loaded: ${res.commands_added}` + 
        (res.commands_failed > 0 ? `\nFailed to convert: ${res.commands_failed}` : '');
      alert(msg);
      await this._loadData();
    } else {
      alert('Failed to add device: ' + (res.error || 'Unknown error'));
    }
  }

  async _sendCommand(deviceId, commandName) {
    const res = await this._api('/api/omniremote/test', 'POST', {
      action: 'test_command',
      device_id: deviceId,
      command_name: commandName
    });
    
    if (!res.success) {
      console.warn('[OmniRemote] Command may have failed:', res);
    }
  }

  async _testCommand(deviceId, commandName) {
    // Show loading indicator
    const btn = event.target.closest('button');
    const originalContent = btn.innerHTML;
    btn.innerHTML = '<ha-icon icon="mdi:loading" class="spin"></ha-icon>';
    
    const res = await this._api('/api/omniremote/test', 'POST', {
      action: 'test_command',
      device_id: deviceId,
      command_name: commandName
    });
    
    // Restore button
    btn.innerHTML = originalContent;
    
    // Show result
    const resultHtml = `
      <div class="modal-content" style="max-width:500px;">
        <h3>Test Result</h3>
        <div style="background:${res.success ? 'rgba(0,200,0,0.1)' : 'rgba(200,0,0,0.1)'};padding:16px;border-radius:8px;margin-bottom:16px;">
          <p style="margin:0;font-size:18px;color:${res.success ? 'var(--success-color)' : 'var(--error-color)'};">
            <ha-icon icon="${res.success ? 'mdi:check-circle' : 'mdi:alert-circle'}"></ha-icon>
            ${res.success ? 'Command Sent Successfully' : 'Command Failed'}
          </p>
        </div>
        <table style="width:100%;font-size:13px;">
          <tr><td style="color:#888;">Device:</td><td>${res.device || deviceId}</td></tr>
          <tr><td style="color:#888;">Command:</td><td>${commandName}</td></tr>
          <tr><td style="color:#888;">Protocol:</td><td>${res.protocol || 'unknown'}</td></tr>
          <tr><td style="color:#888;">Has Broadlink Code:</td><td>${res.has_broadlink_code ? 'Yes' : 'No'}</td></tr>
          ${res.error ? `<tr><td style="color:#888;">Error:</td><td style="color:var(--error-color);">${res.error}</td></tr>` : ''}
        </table>
        <div style="margin-top:16px;text-align:right;">
          <button class="btn btn-p" data-action="close-modal">Close</button>
        </div>
      </div>
    `;
    
    this._modal = resultHtml;
    this._render();
  }

  async _showSwitchProfileModal(deviceId, brand) {
    // Get list of profiles for this brand
    const res = await this._api('/api/omniremote/test', 'POST', {
      action: 'list_profiles',
      brand: brand
    });
    
    const profiles = res.profiles || [];
    const device = this._data.devices.find(d => d.id === deviceId);
    const currentProfile = device?.catalog_id || '';
    
    this._modal = `
      <div class="modal-content" style="max-width:600px;">
        <h3>Switch IR Code Profile</h3>
        <p style="color:#888;">Select a different profile if the current codes don't work with your device.</p>
        
        <div style="margin-bottom:16px;">
          <label class="fl">Current Profile</label>
          <input type="text" class="fi" value="${currentProfile || 'None'}" disabled>
        </div>
        
        <div style="margin-bottom:16px;">
          <label class="fl">Available Profiles for ${brand || 'this brand'}</label>
          <div style="max-height:300px;overflow-y:auto;border:1px solid var(--divider-color);border-radius:4px;">
            ${profiles.length === 0 ? '<p style="padding:16px;color:#888;">No alternate profiles found</p>' :
              profiles.map(p => `
                <div style="padding:12px;border-bottom:1px solid var(--divider-color);display:flex;justify-content:space-between;align-items:center;${p.id === currentProfile ? 'background:rgba(100,100,255,0.1);' : ''}">
                  <div>
                    <strong>${p.name}</strong>
                    <p style="margin:0;font-size:12px;color:#888;">${p.command_count} commands • ${p.id}</p>
                  </div>
                  <div style="display:flex;gap:8px;">
                    <button class="btn btn-s btn-sm" data-action="test-catalog-cmd" data-profile-id="${p.id}" data-cmd="power">Test</button>
                    ${p.id !== currentProfile ? 
                      `<button class="btn btn-p btn-sm" data-action="switch-profile" data-device-id="${deviceId}" data-profile-id="${p.id}">Use This</button>` 
                      : '<span style="color:var(--success-color);font-size:12px;">Current</span>'}
                  </div>
                </div>
              `).join('')
            }
          </div>
        </div>
        
        <p style="font-size:12px;color:#888;margin-top:16px;">
          <ha-icon icon="mdi:information-outline" style="font-size:14px;"></ha-icon>
          Profiles differ by TV year, model series, or region. Try different profiles if commands don't work.
        </p>
        
        <div style="margin-top:16px;text-align:right;">
          <button class="btn btn-s" data-action="close-modal">Cancel</button>
        </div>
      </div>
    `;
    this._render();
  }

  async _switchProfile(deviceId, profileId) {
    const res = await this._api('/api/omniremote/test', 'POST', {
      action: 'switch_profile',
      device_id: deviceId,
      profile_id: profileId
    });
    
    if (res.success) {
      alert(`Switched to profile: ${profileId}\nCommands loaded: ${res.commands_loaded}`);
      this._modal = null;
      await this._loadData();
      this._render();
    } else {
      alert('Failed to switch profile: ' + (res.error || 'Unknown error'));
    }
  }

  async _testCatalogCommand(profileId, commandName) {
    const res = await this._api('/api/omniremote/test', 'POST', {
      action: 'test_catalog',
      profile_id: profileId,
      command_name: commandName
    });
    
    if (res.success) {
      alert('Command sent successfully!');
    } else {
      alert('Test failed: ' + (res.error || 'Unknown error'));
    }
  }

  _showLearnCodeModal(deviceId) {
    this._modal = `
      <div class="modal-content" style="max-width:400px;">
        <h3>Learn IR Code</h3>
        <p>Point your remote at the IR blaster and press the button you want to learn.</p>
        
        <div class="fg">
          <label class="fl">Command Name</label>
          <input type="text" class="fi" id="learn-cmd-name" placeholder="e.g., volume_up">
        </div>
        
        <div style="margin-top:16px;text-align:center;">
          <button class="btn btn-p" id="start-learn" data-device-id="${deviceId}">
            <ha-icon icon="mdi:record"></ha-icon> Start Learning
          </button>
        </div>
        
        <div id="learn-status" style="margin-top:16px;text-align:center;display:none;">
          <ha-icon icon="mdi:loading" class="spin"></ha-icon>
          <p>Waiting for IR signal...</p>
        </div>
        
        <div style="margin-top:16px;text-align:right;">
          <button class="btn btn-s" data-action="close-modal">Cancel</button>
        </div>
      </div>
    `;
    this._render();
    
    // Add learn button handler
    setTimeout(() => {
      const btn = this.shadowRoot.getElementById('start-learn');
      if (btn) {
        btn.addEventListener('click', () => this._startLearning(deviceId));
      }
    }, 100);
  }

  async _startLearning(deviceId) {
    const cmdName = this.shadowRoot.getElementById('learn-cmd-name')?.value?.trim();
    if (!cmdName) {
      alert('Please enter a command name');
      return;
    }
    
    const status = this.shadowRoot.getElementById('learn-status');
    const btn = this.shadowRoot.getElementById('start-learn');
    if (status) status.style.display = 'block';
    if (btn) btn.style.display = 'none';
    
    const res = await this._api('/api/omniremote/learn', 'POST', {
      device_id: deviceId,
      command_name: cmdName,
      timeout: 15
    });
    
    if (res.success) {
      alert('Code learned successfully!');
      this._modal = null;
      await this._loadData();
      this._render();
    } else {
      if (status) status.style.display = 'none';
      if (btn) btn.style.display = 'inline-flex';
      alert('Learning failed: ' + (res.error || 'No IR signal received'));
    }
  }
}

customElements.define('omniremote-panel', OmniRemotePanel);
