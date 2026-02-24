/**
 * OmniRemote Manager Panel v1.3.0
 * Uses event delegation for reliable button handling in Shadow DOM
 */

const OMNIREMOTE_VERSION = "1.3.0";

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
        this._showSceneEditor(this._editingScene?.id);
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
      case 'open-device':
        this._view = 'device';
        this._deviceId = data.deviceId;
        this._render();
        break;
    }
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
    return `<div class="grid">${(this._data.catalog || []).slice(0, 20).map(d => `
      <div class="card">
        <div class="card-head">
          <div class="card-icon"><ha-icon icon="${this._catIcon(d.category)}"></ha-icon></div>
          <div class="card-info">
            <div class="card-title">${d.name}</div>
            <div class="card-sub">${d.brand} • ${Object.keys(d.commands || {}).length} cmds</div>
          </div>
        </div>
        <div class="card-btns">
          <button class="btn btn-p" data-action="add-catalog" data-catalog-id="${d.id}"><ha-icon icon="mdi:plus"></ha-icon>Add</button>
        </div>
      </div>
    `).join('')}</div>`;
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
    return `
      <div class="card" style="max-width:600px;">
        <h3 style="margin-top:0;">${device.name}</h3>
        <p style="color:#888;">${device.brand || ''} ${device.model || ''}</p>
        <h4>Commands (${cmds.length})</h4>
        <div style="display:flex;flex-wrap:wrap;gap:8px;">
          ${cmds.map(c => `<button class="btn btn-s" data-action="send-cmd" data-device-id="${device.id}" data-cmd="${c}">${c}</button>`).join('')}
        </div>
      </div>
    `;
  }

  _catIcon(cat) {
    const icons = { tv:'mdi:television', projector:'mdi:projector', receiver:'mdi:speaker', soundbar:'mdi:soundbar', streaming:'mdi:cast', cable_box:'mdi:set-top-box', ac:'mdi:air-conditioner', fan:'mdi:fan', light:'mdi:lightbulb' };
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

  _showSceneEditor(sceneId = null) {
    const scene = sceneId ? this._data.scenes.find(s => s.id === sceneId) : null;
    const isEdit = !!scene;
    
    // Store current editing state
    this._editingScene = scene ? JSON.parse(JSON.stringify(scene)) : {
      name: '',
      icon: 'mdi:television',
      room_id: null,
      blaster_id: null,
      controlled_device_ids: [],
      controlled_entity_ids: [],
      on_actions: [],
      off_actions: []
    };
    
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
        <select class="fi" id="action-type" onchange="this.getRootNode().host._updateActionTypeUI()">
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
        const commands = selectedDevice?.codes?.map(c => c.name) || [];
        
        return `
          <label class="fl">Device</label>
          <select class="fi" id="action-device">
            <option value="">-- Select Device --</option>
            ${this._data.devices.map(d => `<option value="${d.id}" ${action.device_id === d.id ? 'selected' : ''}>${d.name}</option>`).join('')}
          </select>
          
          <label class="fl" style="margin-top:12px;">Command</label>
          <select class="fi" id="action-command">
            <option value="">-- Select Command --</option>
            ${commands.map(c => `<option value="${c}" ${action.command_name === c ? 'selected' : ''}>${c}</option>`).join('')}
          </select>
        `;
        
      case 'ha_service':
        return `
          <label class="fl">Entity</label>
          <select class="fi" id="action-entity">
            <option value="">-- Select Entity --</option>
            ${(this._data.haEntities || []).map(e => `<option value="${e.entity_id}" ${action.entity_id === e.entity_id ? 'selected' : ''}>${e.name} (${e.domain})</option>`).join('')}
          </select>
          
          <label class="fl" style="margin-top:12px;">Service</label>
          <select class="fi" id="action-service">
            <option value="">-- Select Service --</option>
            <option value="turn_on" ${action.ha_service?.includes('turn_on') ? 'selected' : ''}>Turn On</option>
            <option value="turn_off" ${action.ha_service?.includes('turn_off') ? 'selected' : ''}>Turn Off</option>
            <option value="toggle" ${action.ha_service?.includes('toggle') ? 'selected' : ''}>Toggle</option>
            <option value="select_source" ${action.ha_service?.includes('select_source') ? 'selected' : ''}>Select Source</option>
            <option value="volume_set" ${action.ha_service?.includes('volume_set') ? 'selected' : ''}>Set Volume</option>
          </select>
        `;
        
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

  _removeAction(type, idx) {
    const actions = type === 'on' ? this._editingScene.on_actions : this._editingScene.off_actions;
    actions.splice(idx, 1);
    this._showSceneEditor(this._editingScene.id);
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
    
    // Return to scene editor
    this._showSceneEditor(this._editingScene.id);
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
      alert('Added: ' + res.device.name);
      await this._loadData();
    }
  }
}

customElements.define('omniremote-panel', OmniRemotePanel);
