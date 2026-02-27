/**
 * OmniRemote Manager Panel v1.7.0
 * Uses event delegation for reliable button handling in Shadow DOM
 */

const OMNIREMOTE_VERSION = "1.9.6";

class OmniRemotePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._data = { rooms: [], devices: [], scenes: [], blasters: [], haBlasters: [], catalog: [], remoteProfiles: [], remoteTemplates: [] };
    this._view = 'dashboard';
    this._modal = null;
    this._roomId = null;
    this._deviceId = null;
    this._version = OMNIREMOTE_VERSION;
    
    // Remote Builder state
    this._builderProfileId = null;
    this._builderProfile = null;
    this._builderSelectedButton = null;
    this._builderPreviewMode = false;
    
    // Log panel load for debugging cache issues
    console.log(`[OmniRemote] Panel v${OMNIREMOTE_VERSION} loaded at ${new Date().toISOString()}`);
    console.log(`[OmniRemote] Script URL: ${document.currentScript?.src || 'inline/unknown'}`);
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
      // Add cache-bust to version check
      const res = await fetch(`/api/omniremote/version?_=${Date.now()}`, {
        headers: { 'Cache-Control': 'no-cache' }
      }).then(r => r.json());
      
      if (res.version && res.version !== this._version) {
        console.warn(`[OmniRemote] Version mismatch! Panel: ${this._version}, Server: ${res.version}`);
        this._versionMismatch = res.version;
        this._render();
      }
    } catch (e) {
      console.debug('[OmniRemote] Version check failed:', e);
    }
  }

  _forceReload() {
    // Clear all caches and force reload
    if ('caches' in window) {
      caches.keys().then(names => {
        names.forEach(name => caches.delete(name));
      });
    }
    // Force hard reload bypassing cache
    window.location.href = window.location.href.split('?')[0] + '?_reload=' + Date.now();
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
        this._api('/api/omniremote/physical_remotes'),
        this._api('/api/omniremote/remote_bridges'),
        this._api('/api/omniremote/remote_profiles'),
        this._api('/api/omniremote/debug'),
        this._api('/api/omniremote/flipper'),
      ]);
      
      this._data = {
        rooms: results[0]?.rooms || [],
        devices: results[1]?.devices || [],
        scenes: results[2]?.scenes || [],
        haEntities: results[2]?.ha_entities || [],
        blasters: results[3]?.blasters || [],
        haBlasters: results[3]?.ha_blasters || [],
        catalog: results[4]?.devices || [],
        physicalRemotes: results[5]?.remotes || [],
        remoteBridges: results[6]?.bridges || [],
        remoteProfiles: results[7]?.profiles || [],
        remoteTemplates: results[7]?.templates || [],
        builtinProfiles: results[7]?.builtin_profiles || [],
        dbOk: results[3]?.database_available !== false,
        flippers: results[9]?.devices || [],
      };
      
      // Store debug log separately (can get large)
      this._debugLog = results[8]?.log || [];
      
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
        .version-banner { background:#3d2c1a; border:1px solid #ff9800; padding:12px 24px; display:flex; align-items:center; gap:12px; color:#ffcc80; }
        .version-banner ha-icon { color:#ff9800; }
        .version-banner a { color:#ffb74d; font-weight:500; text-decoration:underline; }
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
        
        /* Status badges */
        .status { display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:500; }
        .status.online { background:#1b3d1b; color:#4caf50; }
        .status.offline { background:#3d1b1b; color:#f44336; }
        .card.offline { opacity:0.7; }
        
        /* Section header */
        .section-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
        .section-header h3 { margin:0; display:flex; align-items:center; gap:8px; }
        
        /* Page header */
        .page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }
        .page-header h2 { margin:0; display:flex; align-items:center; gap:10px; }
        
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
        
        /* Category tiles */
        .category-tile:hover { transform:translateY(-4px); box-shadow:0 8px 24px rgba(0,0,0,0.3); }
        .category-tile:active { transform:translateY(-2px); }
        
        /* Debug log styling */
        #debug-log::-webkit-scrollbar { width:8px; }
        #debug-log::-webkit-scrollbar-track { background:#111; }
        #debug-log::-webkit-scrollbar-thumb { background:#333; border-radius:4px; }
        #debug-log::-webkit-scrollbar-thumb:hover { background:#444; }
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
            <div class="nav-item ${this._view === 'remotes' ? 'active' : ''}" data-nav="remotes">
              <ha-icon icon="mdi:remote"></ha-icon>Physical Remotes
            </div>
            <div class="nav-item ${this._view === 'builder' ? 'active' : ''}" data-nav="builder">
              <ha-icon icon="mdi:palette"></ha-icon>Remote Builder
              <span class="badge">${this._data.remoteProfiles?.length || 0}</span>
            </div>
            <div class="nav-item ${this._view === 'debugger' ? 'active' : ''}" data-nav="debugger">
              <ha-icon icon="mdi:bug"></ha-icon>IR Debugger
            </div>
            <div class="nav-item ${this._view === 'wiki' ? 'active' : ''}" data-nav="wiki">
              <ha-icon icon="mdi:help-circle"></ha-icon>Help & Wiki
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
            <div class="version-banner" style="background:#ff5722;padding:16px;margin-bottom:16px;border-radius:8px;display:flex;align-items:center;gap:12px;">
              <ha-icon icon="mdi:alert" style="font-size:32px;"></ha-icon>
              <div style="flex:1;">
                <strong style="font-size:16px;">Panel Update Required!</strong><br>
                <span style="font-size:13px;">Panel: v${this._version} → Server: v${this._versionMismatch}</span>
              </div>
              <button class="btn" onclick="window.location.href=window.location.href.split('?')[0]+'?_reload='+Date.now();" 
                      style="background:#fff;color:#ff5722;font-weight:bold;padding:12px 24px;">
                <ha-icon icon="mdi:refresh"></ha-icon> Reload Panel
              </button>
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
    
    // Event delegation for dynamically created content in modals
    const modalEl = root.querySelector('.modal');
    if (modalEl) {
      modalEl.addEventListener('click', async (e) => {
        const btn = e.target.closest('[data-action="import-ha-entity"]');
        if (btn) {
          e.stopPropagation();
          const entityId = btn.dataset.entityId;
          console.log('[OmniRemote] Import button clicked via delegation:', entityId);
          if (entityId) {
            await this._importHaEntity(entityId);
          }
        }
        
        // Handle Bluetooth device selection
        const btBtn = e.target.closest('[data-action="bt-select-device"]');
        if (btBtn) {
          e.stopPropagation();
          // Handler is already attached in _showAddRemoteModal
        }
      });
    }
    
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
    
    // Debugger input handlers
    if (this._view === 'debugger') {
      this._setupDebuggerInputs();
    }
  }

  async _handleAction(action, data) {
    console.log('[OmniRemote] Action:', action, data);
    
    switch (action) {
      case 'refresh-data':
        console.log('[OmniRemote] Refreshing data...');
        await this._loadData();
        break;

      // Builder actions
      case 'builder-new':
      case 'builder-create-blank':
      case 'builder-from-template':
      case 'builder-edit':
      case 'builder-duplicate':
      case 'builder-delete':
      case 'builder-back':
      case 'builder-save':
      case 'builder-preview':
      case 'builder-add-button':
      case 'builder-select-button':
      case 'builder-delete-button':
      case 'builder-quick-add':
      case 'builder-apply-props':
      case 'builder-settings':
      case 'builder-clear':
      case 'builder-pick-icon':
        await this._handleBuilderAction(action, data);
        break;

      case 'apply-grid-settings':
        if (this._builderProfile) {
          this._builderProfile.rows = parseInt(this.shadowRoot.getElementById('grid-rows')?.value) || 8;
          this._builderProfile.cols = parseInt(this.shadowRoot.getElementById('grid-cols')?.value) || 4;
          this._builderProfile.device_type = this.shadowRoot.getElementById('grid-device-type')?.value || 'universal';
          this._builderProfile.icon = this.shadowRoot.getElementById('grid-icon')?.value || 'mdi:remote';
          this._builderProfile.description = this.shadowRoot.getElementById('grid-description')?.value || '';
          this._modal = null;
          this._render();
        }
        break;

      case 'show-add-room':
        this._showAddRoomModal();
        break;
      case 'save-room':
        await this._saveRoom();
        break;
      case 'show-add-device':
        this._showAddDeviceModal();
        break;
      case 'show-import-ha-entity':
        await this._showImportHaEntityModal();
        break;
      case 'import-ha-entity':
        await this._importHaEntity(data.entityId);
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
      
      // Flipper Zero actions
      case 'flipper-discover':
        await this._flipperDiscover('all');
        break;
      case 'flipper-discover-usb':
        await this._flipperDiscover('usb');
        break;
      case 'flipper-discover-ble':
        await this._flipperDiscover('bluetooth');
        break;
      case 'flipper-connect':
        await this._flipperConnect(data.flipperId);
        break;
      case 'flipper-disconnect':
        await this._flipperDisconnect(data.flipperId);
        break;
      case 'flipper-remove':
        await this._flipperRemove(data.flipperId);
        break;
      case 'flipper-test':
        await this._flipperTest(data.flipperId);
        break;
      case 'flipper-files':
        await this._flipperShowFiles(data.flipperId);
        break;
      case 'flipper-add':
        await this._flipperAdd(data);
        break;
      
      // Remote Profile Builder actions
      case 'new-profile':
        this._showProfileEditor();
        break;
      case 'create-from-template':
        this._showProfileEditor(null, data.template);
        break;
      case 'edit-profile':
        this._showProfileEditor(data.profileId);
        break;
      case 'duplicate-profile':
        await this._duplicateProfile(data.profileId);
        break;
      case 'delete-profile':
        await this._deleteProfile(data.profileId);
        break;
      case 'preview-profile':
        this._previewProfile(data.profileId);
        break;
      case 'preview-editing-profile':
        this._previewProfile(null, this._editingProfile);
        break;
      case 'save-profile':
        await this._saveProfile();
        break;
      case 'resize-grid':
        this._resizeProfileGrid();
        break;
      case 'clear-grid':
        if (confirm('Clear all buttons from this layout?')) {
          this._editingProfile.buttons = [];
          this._updateProfileEditorGrid();
        }
        break;
      case 'import-profile':
        this._showImportProfileModal();
        break;
      case 'export-profile':
        this._exportProfile(data.profileId);
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
      
      // Icon picker actions
      case 'show-icon-picker':
        this._toggleIconPicker(true);
        break;
      case 'close-icon-picker':
        this._toggleIconPicker(false);
        break;
      case 'pick-icon':
        this._selectIcon(data.icon);
        break;
      case 'apply-custom-icon':
        this._applyCustomIcon();
        break;
      
      // Wiki navigation
      case 'wiki-section':
        this._wikiSection = data.section;
        this._render();
        break;
      
      // Room management actions
      case 'room-add-item':
        this._showRoomAddItemModal(data.roomId);
        break;
      case 'room-add-scene':
        this._showSceneEditor();
        // Pre-select the room
        setTimeout(() => {
          const roomSelect = this.shadowRoot.getElementById('scene-room');
          if (roomSelect) roomSelect.value = data.roomId;
          if (this._editingScene) this._editingScene.room_id = data.roomId;
        }, 100);
        break;
      case 'room-add-device':
        this._showAddDeviceModal(data.roomId);
        break;
      case 'room-add-entity':
        this._showAddHAEntityModal(data.roomId);
        break;
      case 'edit-room':
        this._showEditRoomModal(data.roomId);
        break;
      case 'quick-power':
        await this._sendQuickPower(data.deviceId);
        break;
      
      // HA Entity actions
      case 'call-ha-service':
        await this._callHAService(data.entityId, data.service);
        break;
      case 'search-ha-entities':
        this._filterHAEntities();
        break;
      case 'add-entity-to-room':
        await this._addEntityToRoom(data.entityId, data.roomId);
        break;
      case 'remove-entity-from-room':
        await this._removeEntityFromRoom(data.entityId, data.roomId);
        break;
      case 'set-entity-type':
        this._setEntityDeviceType(data.entityId, data.deviceType);
        break;
      case 'delete-room':
        await this._deleteRoom(data.roomId);
        break;
      case 'save-room-edit':
        await this._saveRoomEdit(data.roomId);
        break;
      
      // Catalog category navigation
      case 'select-category':
        this._catalogFilter = this._catalogFilter || {};
        this._catalogFilter.category = data.category;
        this._catalogFilter.brand = '';
        this._catalogFilter.search = '';
        this._render();
        break;
      case 'clear-category':
        this._catalogFilter = this._catalogFilter || {};
        this._catalogFilter.category = '';
        this._catalogFilter.brand = '';
        this._catalogFilter.search = '';
        this._render();
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
      
      // Physical Remotes actions
      case 'add-remote':
        this._showAddRemoteModal(data.type);
        break;
      case 'edit-remote':
        this._showEditRemoteModal(data.remoteId);
        break;
      case 'delete-remote':
        await this._deleteRemote(data.remoteId);
        break;
      case 'map-buttons':
        this._showButtonMappingModal(data.remoteId);
        break;
      case 'discover-remotes':
        await this._discoverRemotes();
        break;
      case 'save-remote':
        await this._saveRemote();
        break;
      case 'save-button-mapping':
        await this._saveButtonMapping();
        break;
      
      // Bridge actions
      case 'add-bridge':
        this._showAddBridgeModal();
        break;
      case 'edit-bridge':
        this._showEditBridgeModal(data.bridgeId);
        break;
      case 'delete-bridge':
        await this._deleteBridge(data.bridgeId);
        break;
      case 'save-bridge':
        await this._saveBridge();
        break;
      
      // Debugger actions
      case 'refresh-debug-log':
        await this._refreshDebugLog();
        break;
      case 'clear-debug-log':
        await this._clearDebugLog();
        break;
      case 'check-blasters':
        await this._checkBlasterStatus();
        break;
      case 'test-encode':
        await this._testEncode();
        break;
      case 'test-send-debug':
        await this._testSendDebug();
        break;
      case 'quick-test':
        await this._quickTest(data.protocol, data.addr, data.cmd);
        break;
      case 'toggle-encoding-help':
        this._showEncodingHelp = !this._showEncodingHelp;
        this._render();
        break;
      case 'test-catalog-cmd':
        // Called from catalog preview - uses profileId
        await this._testCatalogCommand(data.profileId, data.cmd);
        break;
      case 'debug-catalog-test':
        // Called from debugger - uses deviceId
        console.log('[OmniRemote] debug-catalog-test data:', data);
        await this._debugCatalogTest(data.deviceId, data.cmd);
        break;
    }
  }

  _setupDebuggerInputs() {
    // Setup debugger-specific input handlers
    const blasterSelect = this.shadowRoot.getElementById('debug-blaster');
    const categorySelect = this.shadowRoot.getElementById('debug-category');
    const deviceSelect = this.shadowRoot.getElementById('debug-device');
    
    if (blasterSelect) {
      blasterSelect.addEventListener('change', () => {
        this._debugBlaster = blasterSelect.value;
      });
    }
    
    if (categorySelect) {
      categorySelect.addEventListener('change', () => {
        this._debugCategory = categorySelect.value;
        this._debugDevice = '';  // Reset device selection
        this._render();
      });
    }
    
    if (deviceSelect) {
      deviceSelect.addEventListener('change', () => {
        this._debugDevice = deviceSelect.value;
        this._render();
      });
    }
    
    // Prevent HA keyboard shortcuts in debug inputs
    ['debug-address', 'debug-command'].forEach(id => {
      const input = this.shadowRoot.getElementById(id);
      if (input) {
        input.addEventListener('keydown', e => e.stopPropagation());
        input.addEventListener('keyup', e => e.stopPropagation());
        input.addEventListener('keypress', e => e.stopPropagation());
      }
    });
  }

  _setupCatalogFilters() {
    const search = this.shadowRoot.getElementById('catalog-search');
    const category = this.shadowRoot.getElementById('catalog-category');
    const brand = this.shadowRoot.getElementById('catalog-brand');
    
    if (search) {
      // Prevent HA keyboard shortcuts from firing when typing
      search.addEventListener('keydown', (e) => {
        e.stopPropagation();
      });
      search.addEventListener('keyup', (e) => {
        e.stopPropagation();
      });
      search.addEventListener('keypress', (e) => {
        e.stopPropagation();
      });
      
      // Debounced search to avoid constant re-renders
      let searchTimeout;
      search.addEventListener('input', (e) => {
        e.stopPropagation();
        clearTimeout(searchTimeout);
        const value = search.value;
        searchTimeout = setTimeout(() => {
          this._catalogFilter = this._catalogFilter || {};
          this._catalogFilter.search = value;
          this._catalogSearchFocus = true;  // Remember to refocus
          this._render();
        }, 300);
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
    
    // Refocus search if it was focused before render
    if (this._catalogSearchFocus && search) {
      search.focus();
      search.setSelectionRange(search.value.length, search.value.length);
      this._catalogSearchFocus = false;
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
      remotes: 'Physical Remotes',
      builder: this._builderProfileId ? (this._builderProfile?.name || 'Edit Remote') : 'Remote Builder',
      debugger: 'IR Debugger',
      wiki: 'Help & Wiki',
      room: this._data.rooms.find(r => r.id === this._roomId)?.name || 'Room',
      device: this._data.devices.find(d => d.id === this._deviceId)?.name || 'Device',
    };
    return titles[this._view] || 'Dashboard';
  }

  _getHeaderButtons() {
    // Refresh button for all views
    const refreshBtn = `<button class="btn btn-s" data-action="refresh-data" title="Refresh Data"><ha-icon icon="mdi:refresh"></ha-icon></button>`;
    
    switch (this._view) {
      case 'devices':
        return `<button class="btn btn-p" data-action="show-add-device"><ha-icon icon="mdi:plus"></ha-icon>Add Device</button> ${refreshBtn}`;
      case 'scenes':
        return `<button class="btn btn-p" data-action="show-add-scene"><ha-icon icon="mdi:plus"></ha-icon>Add Scene</button> ${refreshBtn}`;
      case 'blasters':
        return `
          <button class="btn btn-p" data-action="discover"><ha-icon icon="mdi:magnify"></ha-icon>Discover</button>
          <button class="btn btn-s" data-action="discover-mdns" style="margin-left:8px;"><ha-icon icon="mdi:access-point-network"></ha-icon>mDNS</button>
          <button class="btn btn-s" data-action="show-add-blaster" style="margin-left:8px;"><ha-icon icon="mdi:plus"></ha-icon>Add by IP</button>
          ${refreshBtn}
        `;
      case 'builder':
        if (this._builderProfileId) {
          return `
            <button class="btn btn-s" data-action="builder-back"><ha-icon icon="mdi:arrow-left"></ha-icon>Back</button>
            <button class="btn btn-p" data-action="builder-save" style="margin-left:8px;"><ha-icon icon="mdi:content-save"></ha-icon>Save Profile</button>
            <button class="btn btn-s" data-action="builder-preview" style="margin-left:8px;"><ha-icon icon="mdi:eye"></ha-icon>Preview</button>
            ${refreshBtn}
          `;
        }
        return `<button class="btn btn-p" data-action="builder-new"><ha-icon icon="mdi:plus"></ha-icon>New Remote</button> ${refreshBtn}`;
      case 'dashboard':
        return refreshBtn;
      case 'room':
        return `<button class="btn btn-p" data-action="show-add-room-item"><ha-icon icon="mdi:plus"></ha-icon>Add Item</button> ${refreshBtn}`;
      default:
        return refreshBtn;
    }
  }

  _getContent() {
    switch (this._view) {
      case 'dashboard': return this._dashboardView();
      case 'devices': return this._devicesView();
      case 'scenes': return this._scenesView();
      case 'blasters': return this._blastersView();
      case 'catalog': return this._catalogView();
      case 'remotes': return this._remotesView();
      case 'builder': return this._builderView();
      case 'debugger': return this._debuggerView();
      case 'wiki': return this._wikiView();
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
      return `
        <div class="empty">
          <ha-icon icon="mdi:devices"></ha-icon>
          <h3>No Devices</h3>
          <p>Add devices from the IR catalog or import from Home Assistant</p>
          <div style="display:flex;gap:12px;justify-content:center;margin-top:16px;">
            <button class="btn btn-p" data-action="show-add-device">
              <ha-icon icon="mdi:plus"></ha-icon> Add IR Device
            </button>
            <button class="btn btn-s" data-action="show-import-ha-entity">
              <ha-icon icon="mdi:home-assistant"></ha-icon> Import from HA
            </button>
          </div>
        </div>
      `;
    }
    return `
      <div class="page-header" style="margin-bottom:16px;">
        <h2><ha-icon icon="mdi:devices"></ha-icon> Devices</h2>
        <div style="display:flex;gap:8px;">
          <button class="btn btn-s" data-action="show-import-ha-entity">
            <ha-icon icon="mdi:home-assistant"></ha-icon> Import from HA
          </button>
          <button class="btn btn-p" data-action="show-add-device">
            <ha-icon icon="mdi:plus"></ha-icon> Add Device
          </button>
        </div>
      </div>
      <div class="grid">${this._data.devices.map(d => `
        <div class="card">
          <div class="card-head">
            <div class="card-icon" style="${d.entity_id ? 'background:#1b3d1b;' : ''}">
              <ha-icon icon="${d.entity_id ? 'mdi:home-assistant' : this._catIcon(d.category)}" 
                       style="${d.entity_id ? 'color:#4caf50;' : ''}"></ha-icon>
            </div>
            <div class="card-info">
              <div class="card-title">${d.name}</div>
              <div class="card-sub">${d.entity_id || (d.brand || '') + ' ' + (d.model || '')}</div>
            </div>
          </div>
          <div class="card-btns">
            <button class="btn btn-s" data-action="open-device" data-device-id="${d.id}">Control</button>
          </div>
        </div>
      `).join('')}</div>
    `;
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
    const flippers = this._data.flippers || [];
    
    return `
      <div class="page-header">
        <h2><ha-icon icon="mdi:access-point"></ha-icon> IR Blasters</h2>
        <div style="display:flex;gap:8px;">
          <button class="btn btn-p" data-action="discover"><ha-icon icon="mdi:magnify"></ha-icon> Discover</button>
          <button class="btn btn-s" data-action="show-add-blaster"><ha-icon icon="mdi:plus"></ha-icon> Add by IP</button>
        </div>
      </div>
      
      <!-- Broadlink Blasters -->
      <div class="section-header">
        <h3><ha-icon icon="mdi:access-point"></ha-icon> Broadlink Devices</h3>
        <button class="btn btn-sm" data-action="discover-mdns"><ha-icon icon="mdi:access-point-network"></ha-icon> mDNS</button>
      </div>
      ${all.length === 0 ? `
        <div class="card" style="text-align:center;padding:32px;margin-bottom:24px;">
          <ha-icon icon="mdi:access-point-off" style="font-size:48px;color:#666;margin-bottom:16px;display:block;"></ha-icon>
          <p style="color:#888;margin:0;">No Broadlink blasters found. Click Discover to search.</p>
        </div>
      ` : `
        <div class="grid" style="margin-bottom:24px;">
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
        </div>
      `}
      
      <!-- Flipper Zero Section -->
      <div class="section-header">
        <h3><ha-icon icon="mdi:dolphin"></ha-icon> Flipper Zero</h3>
        <button class="btn btn-sm" data-action="flipper-discover"><ha-icon icon="mdi:magnify"></ha-icon> Discover</button>
      </div>
      <div class="card" style="margin-bottom:24px;">
        <p style="color:#888;margin-top:0;font-size:13px;">
          Connect Flipper Zero via USB or Bluetooth to use as an IR blaster and code learner.
        </p>
        ${flippers.length === 0 ? `
          <div style="text-align:center;padding:16px;background:#1a1a2e;border-radius:8px;">
            <ha-icon icon="mdi:dolphin" style="font-size:32px;color:#666;margin-bottom:8px;display:block;"></ha-icon>
            <p style="color:#888;margin:0 0 12px 0;">No Flipper Zero connected</p>
            <button class="btn btn-s" data-action="flipper-discover-usb" style="margin-right:8px;">
              <ha-icon icon="mdi:usb"></ha-icon> Find USB
            </button>
            <button class="btn btn-s" data-action="flipper-discover-ble">
              <ha-icon icon="mdi:bluetooth"></ha-icon> Find Bluetooth
            </button>
          </div>
        ` : `
          <div style="display:flex;flex-direction:column;gap:12px;">
            ${flippers.map(f => `
              <div style="display:flex;align-items:center;gap:12px;padding:12px;background:#1a1a2e;border-radius:8px;">
                <ha-icon icon="${f.connection_type === 'bluetooth' ? 'mdi:bluetooth' : 'mdi:usb'}" 
                         style="font-size:24px;color:${f.connected ? '#4caf50' : '#666'};"></ha-icon>
                <div style="flex:1;">
                  <div style="font-weight:600;">${f.name}</div>
                  <div style="font-size:12px;color:#888;">
                    ${f.port} • ${f.connected ? 'Connected' : 'Disconnected'}
                    ${f.firmware_version ? ' • FW: ' + f.firmware_version : ''}
                  </div>
                </div>
                <div style="display:flex;gap:8px;">
                  ${f.connected ? `
                    <button class="btn btn-sm" data-action="flipper-test" data-flipper-id="${f.id}">
                      <ha-icon icon="mdi:play"></ha-icon> Test
                    </button>
                    <button class="btn btn-sm" data-action="flipper-files" data-flipper-id="${f.id}">
                      <ha-icon icon="mdi:folder"></ha-icon> Files
                    </button>
                    <button class="btn btn-sm btn-danger" data-action="flipper-disconnect" data-flipper-id="${f.id}">
                      Disconnect
                    </button>
                  ` : `
                    <button class="btn btn-sm btn-p" data-action="flipper-connect" data-flipper-id="${f.id}">
                      Connect
                    </button>
                    <button class="btn btn-sm btn-danger" data-action="flipper-remove" data-flipper-id="${f.id}">
                      Remove
                    </button>
                  `}
                </div>
              </div>
            `).join('')}
          </div>
        `}
      </div>
      
      <!-- Flipper Discovery Results (shown after discover) -->
      <div id="flipper-discovered" style="display:none;margin-bottom:24px;">
        <div class="section-header">
          <h3><ha-icon icon="mdi:radar"></ha-icon> Discovered Flippers</h3>
        </div>
        <div id="flipper-discovered-list" class="card"></div>
      </div>
      
      <!-- Help Section -->
      <div class="section-header">
        <h3><ha-icon icon="mdi:help-circle"></ha-icon> About Blasters</h3>
      </div>
      <div class="card">
        <div style="color:#888;font-size:13px;line-height:1.6;">
          <p><strong>Broadlink RM Mini/RM4:</strong> Wi-Fi IR blasters. Discover automatically or add by IP address.</p>
          <p><strong>Home Assistant Entities:</strong> Any <code>remote.*</code> entity from HA integrations (Broadlink, SwitchBot Hub, etc).</p>
          <p><strong>Flipper Zero:</strong> Connect via USB cable or Bluetooth. Can send IR and learn codes from other remotes.</p>
        </div>
      </div>
    `;
  }

  _catalogView() {
    const catalog = this._data.catalog || [];
    const categories = [...new Set(catalog.map(d => d.category))].sort();
    const brands = [...new Set(catalog.map(d => d.brand))].sort();
    
    // Category icons and colors
    const categoryInfo = {
      'tv': { icon: 'mdi:television', color: '#2196f3', label: 'TVs' },
      'receiver': { icon: 'mdi:speaker-multiple', color: '#9c27b0', label: 'Receivers' },
      'soundbar': { icon: 'mdi:soundbar', color: '#e91e63', label: 'Soundbars' },
      'streamer': { icon: 'mdi:cast', color: '#ff5722', label: 'Streamers' },
      'projector': { icon: 'mdi:projector', color: '#795548', label: 'Projectors' },
      'cable': { icon: 'mdi:satellite-variant', color: '#607d8b', label: 'Cable/Satellite' },
      'game_console': { icon: 'mdi:gamepad-variant', color: '#4caf50', label: 'Game Consoles' },
      'bluray': { icon: 'mdi:disc', color: '#3f51b5', label: 'Blu-ray Players' },
      'ac': { icon: 'mdi:air-conditioner', color: '#00bcd4', label: 'Air Conditioners' },
      'fan': { icon: 'mdi:fan', color: '#8bc34a', label: 'Fans' },
      'garage': { icon: 'mdi:garage', color: '#ff9800', label: 'Garage Doors' },
      'lighting': { icon: 'mdi:lightbulb', color: '#ffc107', label: 'Lighting' },
      'radio': { icon: 'mdi:radio', color: '#9e9e9e', label: 'Radios/Car Stereo' },
    };
    
    // Count devices per category
    const categoryCounts = {};
    categories.forEach(cat => {
      categoryCounts[cat] = catalog.filter(d => d.category === cat).length;
    });
    
    // If no category selected, show category tiles
    if (!this._catalogFilter?.category) {
      return `
        <div class="page-header">
          <h2><ha-icon icon="mdi:book-open-variant"></ha-icon> Device Catalog</h2>
          <span style="color:#888;">${catalog.length} devices available</span>
        </div>
        
        <p style="color:#888;margin-bottom:20px;">Select a category to browse pre-built IR code profiles for common devices.</p>
        
        <div class="category-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:16px;">
          ${categories.map(cat => {
            const info = categoryInfo[cat] || { icon: 'mdi:remote', color: '#666', label: cat };
            const count = categoryCounts[cat];
            return `
              <div class="category-tile" data-action="select-category" data-category="${cat}"
                   style="background:linear-gradient(135deg,${info.color}22,${info.color}11);
                          border:1px solid ${info.color}44;border-radius:12px;padding:24px;
                          cursor:pointer;text-align:center;transition:all 0.2s;">
                <ha-icon icon="${info.icon}" style="font-size:48px;color:${info.color};margin-bottom:12px;display:block;"></ha-icon>
                <div style="font-size:16px;font-weight:600;color:#fff;margin-bottom:4px;">${info.label}</div>
                <div style="font-size:13px;color:#888;">${count} device${count !== 1 ? 's' : ''}</div>
              </div>
            `;
          }).join('')}
        </div>
        
        <div style="margin-top:32px;padding-top:24px;border-top:1px solid #333;">
          <h3 style="margin-bottom:16px;"><ha-icon icon="mdi:magnify"></ha-icon> Quick Search</h3>
          <div style="display:flex;gap:12px;flex-wrap:wrap;">
            <input type="text" class="fi" id="catalog-search" placeholder="Search all devices..." 
                   value="${this._catalogFilter?.search || ''}" style="max-width:300px;">
            <select class="fi" id="catalog-brand" style="max-width:150px;">
              <option value="">All Brands</option>
              ${brands.map(b => `<option value="${b}">${b}</option>`).join('')}
            </select>
          </div>
        </div>
      `;
    }
    
    // Category is selected - show devices in that category
    const selectedCat = this._catalogFilter.category;
    const catInfo = categoryInfo[selectedCat] || { icon: 'mdi:remote', color: '#666', label: selectedCat };
    
    // Filter devices
    let filtered = catalog.filter(d => d.category === selectedCat);
    
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
    
    // Get brands for this category
    const catBrands = [...new Set(catalog.filter(d => d.category === selectedCat).map(d => d.brand))].sort();
    
    return `
      <div class="page-header">
        <div style="display:flex;align-items:center;gap:12px;">
          <button class="btn btn-s" data-action="clear-category" style="padding:8px;">
            <ha-icon icon="mdi:arrow-left"></ha-icon>
          </button>
          <ha-icon icon="${catInfo.icon}" style="font-size:32px;color:${catInfo.color};"></ha-icon>
          <div>
            <h2 style="margin:0;">${catInfo.label}</h2>
            <span style="color:#888;font-size:13px;">${filtered.length} of ${categoryCounts[selectedCat]} devices</span>
          </div>
        </div>
      </div>
      
      <div class="catalog-filters" style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;align-items:center;">
        <input type="text" class="fi" id="catalog-search" placeholder="Search ${catInfo.label.toLowerCase()}..." 
               value="${this._catalogFilter?.search || ''}" style="max-width:200px;">
        <select class="fi" id="catalog-brand" style="max-width:150px;">
          <option value="">All Brands</option>
          ${catBrands.map(b => `<option value="${b}" ${this._catalogFilter?.brand === b ? 'selected' : ''}>${b}</option>`).join('')}
        </select>
      </div>
      
      <div class="grid">${filtered.map(d => `
        <div class="card">
          <div class="card-head">
            <div class="card-icon" style="background:${catInfo.color}22;"><ha-icon icon="${catInfo.icon}" style="color:${catInfo.color};"></ha-icon></div>
            <div class="card-info">
              <div class="card-title">${d.name}</div>
              <div class="card-sub">${d.brand} • ${Object.keys(d.commands || d.ir_codes || {}).length} cmds</div>
              ${d.model_years ? `<div class="card-sub">${d.model_years}</div>` : ''}
            </div>
          </div>
          ${d.description ? `<p style="font-size:12px;color:#888;margin:8px 0;line-height:1.4;">${d.description}</p>` : ''}
          <div class="card-btns">
            <button class="btn btn-s" data-action="preview-catalog" data-catalog-id="${d.id}">Preview</button>
            <button class="btn btn-p" data-action="add-catalog" data-catalog-id="${d.id}"><ha-icon icon="mdi:plus"></ha-icon>Add</button>
          </div>
        </div>
      `).join('')}</div>
      
      ${filtered.length === 0 ? `
        <div class="empty" style="padding:40px;">
          <ha-icon icon="mdi:magnify"></ha-icon>
          <h4>No Devices Found</h4>
          <p>Try adjusting your search or filter.</p>
        </div>
      ` : ''}
    `;
  }

  _debuggerView() {
    // IR Command Debugger view
    const blasters = this._data.blasters || [];
    const haBlasters = this._data.haBlasters || [];
    const allBlasters = [...blasters, ...haBlasters];
    const catalog = this._data.catalog || [];
    
    // Get unique categories from catalog
    const categories = [...new Set(catalog.map(d => d.category))].sort();
    
    return `
      <div class="page-header">
        <h2><ha-icon icon="mdi:bug"></ha-icon> IR Command Debugger</h2>
        <div style="display:flex;gap:8px;">
          <button class="btn btn-s" data-action="refresh-debug-log"><ha-icon icon="mdi:refresh"></ha-icon> Refresh</button>
          <button class="btn btn-s" data-action="clear-debug-log"><ha-icon icon="mdi:delete"></ha-icon> Clear Log</button>
        </div>
      </div>
      
      <!-- Blaster Selection -->
      <div class="section-header">
        <h3><ha-icon icon="mdi:access-point"></ha-icon> Select IR Blaster</h3>
        <button class="btn btn-sm" data-action="check-blasters"><ha-icon icon="mdi:refresh"></ha-icon> Check Status</button>
      </div>
      <div class="card" style="margin-bottom:24px;">
        <p style="color:#888;margin-top:0;font-size:13px;">Select which IR blaster to use for testing. All test commands will be sent through the selected blaster.</p>
        ${allBlasters.length === 0 ? `
          <div style="padding:16px;background:#2a1a1a;border:1px solid #f44336;border-radius:8px;color:#ef9a9a;">
            <ha-icon icon="mdi:alert"></ha-icon> No blasters configured. Go to <strong>Blasters</strong> section to add one.
          </div>
        ` : `
          <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;">
            <div class="fg" style="margin:0;flex:1;min-width:200px;">
              <label class="fl">Active Blaster</label>
              <select class="fi" id="debug-blaster">
                <option value="">Auto (first available)</option>
                ${allBlasters.map(b => `
                  <option value="${b.id || b.entity_id}" ${this._debugBlaster === (b.id || b.entity_id) ? 'selected' : ''}>
                    ${b.name} ${b.host ? '(' + b.host + ')' : ''}
                  </option>
                `).join('')}
              </select>
            </div>
            <div id="blaster-status-indicator" style="display:flex;align-items:center;gap:8px;padding:8px 16px;background:#1a1a2e;border-radius:8px;">
              <span class="status-dot" style="width:10px;height:10px;border-radius:50%;background:#666;"></span>
              <span style="color:#888;font-size:13px;">Click "Check Status" to verify</span>
            </div>
          </div>
        `}
      </div>
      
      <!-- Test IR Encoding -->
      <div class="section-header">
        <h3><ha-icon icon="mdi:code-braces"></ha-icon> Test IR Encoding</h3>
        <button class="btn btn-sm" data-action="toggle-encoding-help" style="font-size:11px;"><ha-icon icon="mdi:help-circle"></ha-icon> Help</button>
      </div>
      <div id="encoding-help" class="card" style="margin-bottom:12px;display:${this._showEncodingHelp ? 'block' : 'none'};background:#1a2a1a;border-color:#4caf50;">
        <h4 style="margin-top:0;color:#81c784;"><ha-icon icon="mdi:information"></ha-icon> How to Use Test Encoding</h4>
        <div style="color:#a5d6a7;font-size:13px;line-height:1.6;">
          <p><strong>Protocol:</strong> The IR encoding protocol. Each manufacturer typically uses one:</p>
          <ul style="margin:4px 0 12px 0;padding-left:20px;">
            <li><strong>Samsung32</strong> - Samsung TVs, monitors, home theater (addr: 07)</li>
            <li><strong>NEC</strong> - LG, Vizio, many Asian brands (8-bit address)</li>
            <li><strong>NEC Extended</strong> - LG, some Sony (16-bit address)</li>
            <li><strong>Sony SIRC</strong> - Sony TVs, PlayStation, audio (12/15/20 bit)</li>
            <li><strong>RC5/RC6</strong> - Philips, European brands, some Microsoft</li>
            <li><strong>Panasonic</strong> - Panasonic (Kaseikyo protocol)</li>
            <li><strong>JVC</strong> - JVC audio/video equipment</li>
          </ul>
          <p><strong>Address (hex):</strong> Identifies the device type/brand. Examples:</p>
          <ul style="margin:4px 0 12px 0;padding-left:20px;">
            <li>Samsung TV: <code>07</code></li>
            <li>LG TV: <code>04</code></li>
            <li>Sony TV: <code>01</code></li>
            <li>NEC generic: <code>00</code> or <code>04</code></li>
          </ul>
          <p><strong>Command (hex):</strong> The specific button/function. Common codes:</p>
          <ul style="margin:4px 0 12px 0;padding-left:20px;">
            <li>Power toggle: <code>02</code> (Samsung), <code>08</code> (NEC)</li>
            <li>Power off: <code>98</code> (Samsung discrete)</li>
            <li>Volume up: <code>07</code> (Samsung), <code>02</code> (NEC)</li>
            <li>Volume down: <code>0B</code> (Samsung), <code>03</code> (NEC)</li>
            <li>Mute: <code>0F</code> (Samsung), <code>09</code> (NEC)</li>
          </ul>
          <p style="margin-top:12px;"><strong>Buttons:</strong></p>
          <ul style="margin:4px 0;padding-left:20px;">
            <li><strong>Encode Only</strong> - Convert to Broadlink packet without sending (see bytes in log)</li>
            <li><strong>Send</strong> - Encode AND transmit via selected blaster</li>
          </ul>
          <p style="margin-top:12px;border-top:1px solid #4caf50;padding-top:12px;">
            <strong>Finding codes:</strong> Search "DEVICE_NAME IR codes hex" or check <a href="http://www.hifi-remote.com/wiki/index.php?title=Main_Page" target="_blank" style="color:#81c784;">IRDB Wiki</a>, 
            <a href="https://github.com/probonopd/irdb" target="_blank" style="color:#81c784;">GitHub IRDB</a>, or your device service manual.
          </p>
        </div>
      </div>
      <div class="card" style="margin-bottom:24px;">
        <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;">
          <div class="fg" style="margin:0;">
            <label class="fl">Protocol</label>
            <select class="fi" id="debug-protocol">
              <option value="samsung32">Samsung32</option>
              <option value="nec">NEC</option>
              <option value="nec_ext">NEC Extended</option>
              <option value="sony">Sony SIRC</option>
              <option value="rc5">RC5</option>
              <option value="rc6">RC6</option>
              <option value="panasonic">Panasonic</option>
              <option value="jvc">JVC</option>
            </select>
          </div>
          <div class="fg" style="margin:0;">
            <label class="fl">Address (hex)</label>
            <input type="text" class="fi" id="debug-address" value="07" style="width:80px;" placeholder="07">
          </div>
          <div class="fg" style="margin:0;">
            <label class="fl">Command (hex)</label>
            <input type="text" class="fi" id="debug-command" value="02" style="width:80px;" placeholder="02">
          </div>
          <button class="btn btn-s" data-action="test-encode"><ha-icon icon="mdi:code-tags"></ha-icon> Encode Only</button>
          <button class="btn btn-p" data-action="test-send-debug"><ha-icon icon="mdi:send"></ha-icon> Send</button>
        </div>
        <div id="encode-result" style="margin-top:16px;display:none;">
          <div style="background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:12px;font-family:monospace;font-size:12px;">
            <div id="encode-output"></div>
          </div>
        </div>
      </div>
      
      <!-- Quick Test from Catalog -->
      <div class="section-header">
        <h3><ha-icon icon="mdi:remote"></ha-icon> Quick Test from Catalog</h3>
      </div>
      <div class="card" style="margin-bottom:24px;">
        <p style="color:#888;margin-top:0;font-size:13px;">Test commands from any device in the catalog. Select a device, then click a command to send it.</p>
        <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;margin-bottom:16px;">
          <div class="fg" style="margin:0;flex:1;min-width:150px;">
            <label class="fl">Category</label>
            <select class="fi" id="debug-category">
              <option value="">Select category...</option>
              ${categories.map(c => '<option value="' + c + '"' + (this._debugCategory === c ? ' selected' : '') + '>' + c + '</option>').join('')}
            </select>
          </div>
          <div class="fg" style="margin:0;flex:2;min-width:200px;">
            <label class="fl">Device</label>
            <select class="fi" id="debug-device" ${!this._debugCategory ? 'disabled' : ''}>
              <option value="">Select device...</option>
              ${this._debugCategory ? catalog.filter(d => d.category === this._debugCategory).map(d => 
                '<option value="' + d.id + '"' + (this._debugDevice === d.id ? ' selected' : '') + '>' + d.brand + ' - ' + d.name + '</option>'
              ).join('') : ''}
            </select>
          </div>
        </div>
        <div id="debug-commands" style="display:flex;gap:8px;flex-wrap:wrap;">
          ${this._debugDevice ? (() => {
            const device = catalog.find(d => d.id === this._debugDevice);
            if (!device) return '<span style="color:#888;">Device not found</span>';
            const commands = device.commands || device.ir_codes || {};
            const cmdList = Object.keys(commands).slice(0, 20);
            return cmdList.map(cmd => 
              '<button class="btn" data-action="debug-catalog-test" data-device-id="' + device.id + '" data-cmd="' + cmd + '">' + cmd + '</button>'
            ).join('') + (Object.keys(commands).length > 20 ? '<span style="color:#888;align-self:center;">+' + (Object.keys(commands).length - 20) + ' more</span>' : '');
          })() : '<span style="color:#666;font-style:italic;">Select a category and device above</span>'}
        </div>
      </div>
      
      <!-- Debug Log -->
      <div class="section-header">
        <h3><ha-icon icon="mdi:text-box-outline"></ha-icon> Command Log</h3>
        <span style="color:#888;font-size:12px;">${this._debugLog?.length || 0} entries</span>
      </div>
      <div id="debug-log" style="background:#0d0d1a;border:1px solid #333;border-radius:8px;max-height:400px;overflow-y:auto;">
        ${this._debugLog && this._debugLog.length > 0 ? 
          this._debugLog.slice().reverse().map(entry => '<div style="padding:12px;border-bottom:1px solid #222;font-family:monospace;font-size:12px;">' +
            '<div style="display:flex;justify-content:space-between;margin-bottom:4px;">' +
              '<span style="color:' + (entry.status === 'success' ? '#4caf50' : entry.status === 'error' ? '#f44336' : '#ff9800') + ';">● ' + (entry.action || 'unknown') + '</span>' +
              '<span style="color:#666;">' + (entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : '') + '</span>' +
            '</div>' +
            (entry.protocol ? '<div style="color:#888;">Protocol: <strong>' + entry.protocol + '</strong>, Addr: <strong>0x' + (entry.address || entry.input?.address || '??') + '</strong>, Cmd: <strong>0x' + (entry.command_hex || entry.command || entry.input?.command || '??') + '</strong></div>' : '') +
            (entry.blaster_name ? '<div style="color:#888;">Blaster: <strong>' + entry.blaster_name + '</strong></div>' : '') +
            (entry.error ? '<div style="color:#f44336;margin-top:4px;">Error: ' + entry.error + '</div>' : '') +
            (entry.timings ? '<div style="color:#666;">Timings: ' + entry.timings.count + ' pulses, ' + (entry.timings.total_duration_ms?.toFixed(1) || '?') + 'ms</div>' : '') +
            (entry.output?.broadlink_bytes ? '<div style="color:#666;">Packet: ' + entry.output.broadlink_bytes + ' bytes</div>' : '') +
            (entry.bytes_sent ? '<div style="color:#4caf50;">Sent ' + entry.bytes_sent + ' bytes</div>' : '') +
          '</div>').join('') 
          : '<div style="padding:32px;text-align:center;color:#666;">' +
              '<ha-icon icon="mdi:text-box-outline" style="font-size:48px;margin-bottom:12px;display:block;opacity:0.5;"></ha-icon>' +
              '<p style="margin:0;">No commands logged yet.</p>' +
              '<p style="margin:4px 0 0 0;font-size:12px;">Send a command to see debug output here.</p>' +
            '</div>'
        }
      </div>
      
      <!-- Adding Devices to Catalog -->
      <div class="section-header" style="margin-top:24px;">
        <h3><ha-icon icon="mdi:plus-circle"></ha-icon> Adding Devices to Catalog</h3>
      </div>
      <div class="card" style="margin-bottom:24px;">
        <p style="margin-top:0;color:#888;font-size:13px;">The device catalog includes 94+ built-in IR profiles. To add a custom device:</p>
        <ol style="margin:12px 0;padding-left:20px;color:#ccc;line-height:2;">
          <li><strong>Request via GitHub:</strong> Open an issue with device brand, model, and IR codes</li>
          <li><strong>Use IR Learner:</strong> Go to a device, click Learn Code, capture from your remote</li>
          <li><strong>Import Flipper Zero:</strong> Import .ir files via device options</li>
          <li><strong>Manual Entry:</strong> Add protocol/address/command codes manually</li>
        </ol>
        <p style="margin-bottom:0;color:#666;font-size:12px;">
          Catalog source: <code>custom_components/omniremote/catalog/</code>
        </p>
      </div>
      
      <!-- Troubleshooting Tips -->
      <div class="section-header">
        <h3><ha-icon icon="mdi:lightbulb-outline"></ha-icon> Troubleshooting</h3>
      </div>
      <div class="card">
        <ul style="margin:0;padding-left:20px;color:#888;line-height:1.8;font-size:13px;">
          <li><strong>No response?</strong> Check blaster LED flashes (use phone camera for invisible IR)</li>
          <li><strong>Samsung TV?</strong> Try discrete power_off (0x98) instead of toggle (0x02)</li>
          <li><strong>Nothing happens?</strong> Verify blaster points at device IR receiver</li>
          <li><strong>Wrong device responds?</strong> Try different address values</li>
          <li><strong>Check HA logs:</strong> Filter by "omniremote" for encoding details</li>
        </ul>
      </div>
    `;
  }


  _wikiView() {
    // Wiki section tracker
    this._wikiSection = this._wikiSection || 'getting-started';
    
    const sections = {
      'getting-started': {
        title: 'Getting Started',
        icon: 'mdi:rocket-launch',
        content: `
          <h3>Welcome to OmniRemote</h3>
          <p>OmniRemote is a universal remote control integration for Home Assistant that lets you control IR devices, create automation scenes, and manage physical remotes.</p>
          
          <h4>Quick Start Guide</h4>
          <ol>
            <li><strong>Add a Blaster</strong> - Go to <em>Blasters</em> tab and click <em>Discover</em> to find your Broadlink RM device</li>
            <li><strong>Add Devices</strong> - Browse the <em>Catalog</em> for pre-built device profiles (TVs, receivers, etc.)</li>
            <li><strong>Create Scenes</strong> - Combine multiple commands into ON/OFF sequences</li>
            <li><strong>Control</strong> - Use the Dashboard or create Home Assistant automations</li>
          </ol>
          
          <h4>Supported Hardware</h4>
          <ul>
            <li><strong>Broadlink RM Mini/RM4</strong> - WiFi IR blasters (recommended)</li>
            <li><strong>Flipper Zero</strong> - USB or Bluetooth connection</li>
            <li><strong>Home Assistant Remote Entities</strong> - SwitchBot Hub, Tuya, etc.</li>
          </ul>
        `
      },
      'blasters': {
        title: 'IR Blasters',
        icon: 'mdi:access-point',
        content: `
          <h3>Setting Up IR Blasters</h3>
          
          <h4>Broadlink RM Mini / RM4</h4>
          <ol>
            <li>Setup your Broadlink device using the Broadlink app (just to get it on WiFi)</li>
            <li>In OmniRemote, go to <em>Blasters</em> → <em>Discover</em></li>
            <li>Your device should appear - click to add it</li>
            <li>If not found, click <em>Add by IP</em> and enter the IP address manually</li>
          </ol>
          
          <h4>Flipper Zero</h4>
          <ol>
            <li>Connect Flipper via USB or enable Bluetooth</li>
            <li>In <em>Blasters</em> section, click <em>Find USB</em> or <em>Find Bluetooth</em></li>
            <li>Select your Flipper from discovered devices</li>
            <li>Click <em>Connect</em></li>
          </ol>
          
          <h4>Troubleshooting</h4>
          <ul>
            <li><strong>Device not found:</strong> Check it's on the same network as Home Assistant</li>
            <li><strong>Commands not working:</strong> Make sure the blaster has line-of-sight to the device</li>
            <li><strong>Intermittent issues:</strong> Try assigning a static IP to your blaster</li>
          </ul>
        `
      },
      'devices': {
        title: 'Adding Devices',
        icon: 'mdi:devices',
        content: `
          <h3>Adding Devices to Control</h3>
          
          <h4>From Catalog (Recommended)</h4>
          <ol>
            <li>Go to <em>Catalog</em> tab</li>
            <li>Select a category (TV, Receiver, etc.)</li>
            <li>Find your brand and model</li>
            <li>Click <em>Add Device</em></li>
          </ol>
          <p>Catalog devices come with pre-configured IR codes that should work with most models.</p>
          
          <h4>Manual Device Setup</h4>
          <ol>
            <li>Go to <em>Devices</em> → <em>Add Device</em></li>
            <li>Enter device name, select category</li>
            <li>Add commands using IR Learner or manual entry</li>
          </ol>
          
          <h4>Learning IR Codes</h4>
          <ol>
            <li>Select a device and click <em>Learn Code</em></li>
            <li>Point your original remote at the IR blaster</li>
            <li>Press the button you want to learn</li>
            <li>Name the command and save</li>
          </ol>
          
          <h4>Importing Flipper Zero Files</h4>
          <ol>
            <li>Export .ir files from your Flipper Zero</li>
            <li>In OmniRemote device settings, select <em>Import Flipper IR</em></li>
            <li>Upload the .ir file</li>
          </ol>
        `
      },
      'scenes': {
        title: 'Scenes & Automation',
        icon: 'mdi:play-box-multiple',
        content: `
          <h3>Creating Scenes</h3>
          <p>Scenes let you combine multiple IR commands, HA services, and delays into ON and OFF sequences.</p>
          
          <h4>Scene Example: "Watch TV"</h4>
          <p><strong>ON Sequence:</strong></p>
          <ol>
            <li>TV Power On</li>
            <li>Delay 3 seconds (wait for TV to boot)</li>
            <li>Receiver Power On</li>
            <li>Receiver Input: TV</li>
            <li>Turn off room lights (HA service)</li>
          </ol>
          <p><strong>OFF Sequence:</strong></p>
          <ol>
            <li>TV Power Off</li>
            <li>Receiver Power Off</li>
            <li>Turn on room lights (HA service)</li>
          </ol>
          
          <h4>Action Types</h4>
          <ul>
            <li><strong>IR Command:</strong> Send a command from one of your devices</li>
            <li><strong>HA Service:</strong> Call any Home Assistant service (lights, switches, scripts)</li>
            <li><strong>Delay:</strong> Wait a specified number of seconds</li>
            <li><strong>Network Command:</strong> Send network commands to supported devices</li>
          </ul>
          
          <h4>Using Scenes in Automations</h4>
          <pre style="background:#1a1a2e;padding:12px;border-radius:8px;overflow-x:auto;">
service: omniremote.run_scene
data:
  scene_id: watch_tv
  action: on  # or "off"</pre>
        `
      },
      'ir-codes': {
        title: 'IR Protocols & Codes',
        icon: 'mdi:remote',
        content: `
          <h3>Understanding IR Protocols</h3>
          
          <h4>Common Protocols</h4>
          <table style="width:100%;border-collapse:collapse;margin:16px 0;">
            <tr style="border-bottom:1px solid #333;">
              <th style="text-align:left;padding:8px;">Protocol</th>
              <th style="text-align:left;padding:8px;">Used By</th>
              <th style="text-align:left;padding:8px;">Address Format</th>
            </tr>
            <tr style="border-bottom:1px solid #333;">
              <td style="padding:8px;">Samsung32</td>
              <td style="padding:8px;">Samsung TVs</td>
              <td style="padding:8px;">1 byte (e.g., 07)</td>
            </tr>
            <tr style="border-bottom:1px solid #333;">
              <td style="padding:8px;">NEC</td>
              <td style="padding:8px;">LG, Vizio, Onkyo, most Asian brands</td>
              <td style="padding:8px;">1 byte (e.g., 04, 4B)</td>
            </tr>
            <tr style="border-bottom:1px solid #333;">
              <td style="padding:8px;">Sony SIRC</td>
              <td style="padding:8px;">Sony TVs, PlayStation</td>
              <td style="padding:8px;">5 bits (01 for TV)</td>
            </tr>
            <tr style="border-bottom:1px solid #333;">
              <td style="padding:8px;">RC5/RC6</td>
              <td style="padding:8px;">Philips, European brands</td>
              <td style="padding:8px;">5 bits</td>
            </tr>
            <tr>
              <td style="padding:8px;">Panasonic</td>
              <td style="padding:8px;">Panasonic (Kaseikyo)</td>
              <td style="padding:8px;">2 bytes</td>
            </tr>
          </table>
          
          <h4>Finding IR Codes</h4>
          <ul>
            <li><strong>IRDB Wiki:</strong> <a href="http://www.hifi-remote.com/wiki/" target="_blank" style="color:#64b5f6;">hifi-remote.com/wiki</a></li>
            <li><strong>GitHub IRDB:</strong> <a href="https://github.com/probonopd/irdb" target="_blank" style="color:#64b5f6;">github.com/probonopd/irdb</a></li>
            <li><strong>Device service manual</strong> - Often contains IR code tables</li>
            <li><strong>Use IR Learner</strong> - Capture from your existing remote</li>
          </ul>
          
          <h4>Testing IR Codes</h4>
          <p>Use the <em>IR Debugger</em> tab to test protocol/address/command combinations before adding to devices.</p>
        `
      },
      'troubleshooting': {
        title: 'Troubleshooting',
        icon: 'mdi:wrench',
        content: `
          <h3>Common Issues & Solutions</h3>
          
          <h4>IR Commands Not Working</h4>
          <ul>
            <li><strong>No response at all:</strong> Check blaster connection, line-of-sight, and try moving closer</li>
            <li><strong>Wrong device responds:</strong> Verify the correct address for your device model</li>
            <li><strong>Intermittent:</strong> Some devices need repeat codes - edit command and increase repeat count</li>
          </ul>
          
          <h4>HTTP 401 Unauthorized</h4>
          <p>If you see "HTTP 401: Unauthorized" errors:</p>
          <ol>
            <li>Ensure you're accessing OmniRemote through Home Assistant (not direct API)</li>
            <li>Clear browser cache and hard refresh (Ctrl+Shift+R)</li>
            <li>Update to latest OmniRemote version</li>
          </ol>
          
          <h4>Blaster Not Discovered</h4>
          <ul>
            <li>Ensure blaster is on same network/VLAN as Home Assistant</li>
            <li>Try adding by IP address manually</li>
            <li>Check firewall isn't blocking UDP broadcast (port 80)</li>
          </ul>
          
          <h4>Catalog Device Codes Wrong</h4>
          <p>Manufacturer codes vary by region and model year. Options:</p>
          <ol>
            <li>Try alternate profiles if available (some brands have multiple)</li>
            <li>Use IR Learner to capture codes from your actual remote</li>
            <li>Report incorrect codes via GitHub issue</li>
          </ol>
          
          <h4>Debug Logging</h4>
          <p>Enable detailed logging in configuration.yaml:</p>
          <pre style="background:#1a1a2e;padding:12px;border-radius:8px;overflow-x:auto;">
logger:
  logs:
    custom_components.omniremote: debug</pre>
        `
      },
      'api': {
        title: 'API & Services',
        icon: 'mdi:api',
        content: `
          <h3>Home Assistant Services</h3>
          
          <h4>Send IR Command</h4>
          <pre style="background:#1a1a2e;padding:12px;border-radius:8px;overflow-x:auto;">
service: omniremote.send_command
data:
  device_id: samsung_tv_living_room
  command: power</pre>
          
          <h4>Run Scene</h4>
          <pre style="background:#1a1a2e;padding:12px;border-radius:8px;overflow-x:auto;">
service: omniremote.run_scene
data:
  scene_id: watch_tv
  action: on  # "on" or "off"</pre>
          
          <h4>Send Raw IR Code</h4>
          <pre style="background:#1a1a2e;padding:12px;border-radius:8px;overflow-x:auto;">
service: omniremote.send_raw
data:
  blaster_id: rm_mini_living_room
  protocol: nec
  address: "04"
  command: "08"</pre>
          
          <h3>REST API Endpoints</h3>
          <p>All endpoints are prefixed with <code>/api/omniremote/</code></p>
          <ul>
            <li><code>GET /rooms</code> - List all rooms</li>
            <li><code>GET /devices</code> - List all devices</li>
            <li><code>GET /scenes</code> - List all scenes</li>
            <li><code>GET /blasters</code> - List all blasters</li>
            <li><code>GET /catalog</code> - Browse device catalog</li>
            <li><code>POST /test</code> - Test IR commands</li>
          </ul>
        `
      },
      'about': {
        title: 'About OmniRemote',
        icon: 'mdi:information',
        content: `
          <h3>About OmniRemote</h3>
          <p><strong>Version:</strong> ${this._data.version || 'Unknown'}</p>
          <p>OmniRemote is a universal remote control integration for Home Assistant.</p>
          
          <h4>Features</h4>
          <ul>
            <li>Control IR devices via Broadlink or Flipper Zero</li>
            <li>Pre-built device catalog with 90+ device profiles</li>
            <li>Scene automation with ON/OFF sequences</li>
            <li>IR code learning from existing remotes</li>
            <li>Physical remote support (Zigbee, RF, Bluetooth)</li>
            <li>Network device control (eISCP, HTTP, etc.)</li>
          </ul>
          
          <h4>Links</h4>
          <ul>
            <li><a href="https://github.com/omniremote/omniremote" target="_blank" style="color:#64b5f6;">GitHub Repository</a></li>
            <li><a href="https://github.com/omniremote/omniremote/issues" target="_blank" style="color:#64b5f6;">Report Issues</a></li>
            <li><a href="https://github.com/omniremote/omniremote/discussions" target="_blank" style="color:#64b5f6;">Community Discussions</a></li>
          </ul>
          
          <h4>Credits</h4>
          <p>Built with ❤️ for the Home Assistant community.</p>
          <p>Uses Broadlink protocol implementation and Flipper Zero CLI interface.</p>
        `
      }
    };
    
    const currentSection = sections[this._wikiSection] || sections['getting-started'];
    
    return `
      <div class="wiki-container" style="display:flex;gap:24px;">
        <!-- Wiki Navigation -->
        <div class="wiki-nav" style="width:220px;flex-shrink:0;">
          <div class="card" style="padding:0;">
            ${Object.entries(sections).map(([key, section]) => `
              <div class="wiki-nav-item ${this._wikiSection === key ? 'active' : ''}" 
                   data-action="wiki-section" data-section="${key}"
                   style="display:flex;align-items:center;gap:8px;padding:12px 16px;cursor:pointer;
                          border-bottom:1px solid #333;
                          background:${this._wikiSection === key ? '#2a2a4a' : 'transparent'};
                          color:${this._wikiSection === key ? '#64b5f6' : '#888'};">
                <ha-icon icon="${section.icon}" style="font-size:18px;"></ha-icon>
                <span>${section.title}</span>
              </div>
            `).join('')}
          </div>
        </div>
        
        <!-- Wiki Content -->
        <div class="wiki-content" style="flex:1;min-width:0;">
          <div class="card">
            <div class="wiki-article" style="line-height:1.7;color:#ccc;">
              ${currentSection.content}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  _remotesView() {
    // Physical Remotes view - manage Zigbee, RF, BT, and USB remotes
    const remotes = this._data.physicalRemotes || [];
    const bridges = this._data.remoteBridges || [];
    const rooms = this._data.rooms || [];
    
    const remoteTypeIcons = {
      'zigbee': 'mdi:zigbee',
      'rf_433': 'mdi:access-point',
      'bluetooth': 'mdi:bluetooth',
      'usb_keyboard': 'mdi:usb',
      'ir': 'mdi:remote',
    };
    
    const bridgeTypeIcons = {
      'zigbee_zha': 'mdi:zigbee',
      'zigbee_deconz': 'mdi:zigbee',
      'zigbee_z2m': 'mdi:zigbee',
      'rf_tasmota': 'mdi:access-point',
      'rf_esphome': 'mdi:chip',
      'bluetooth_proxy': 'mdi:bluetooth',
      'usb_bridge': 'mdi:raspberry-pi',
      'network': 'mdi:lan',
    };
    
    return `
      <div class="page-header">
        <h2><ha-icon icon="mdi:remote"></ha-icon> Physical Remotes</h2>
        <div style="display:flex;gap:8px;">
          <button class="btn btn-s" data-action="discover-remotes"><ha-icon icon="mdi:refresh"></ha-icon> Discover</button>
          <button class="btn btn-p" data-action="add-remote"><ha-icon icon="mdi:plus"></ha-icon> Add Remote</button>
        </div>
      </div>
      
      <!-- Bridges Section -->
      <div class="section-header" style="margin-top:20px;">
        <h3><ha-icon icon="mdi:router-wireless"></ha-icon> Bridges & Receivers</h3>
        <button class="btn btn-sm" data-action="add-bridge"><ha-icon icon="mdi:plus"></ha-icon> Add Bridge</button>
      </div>
      <p style="color:#888;margin-bottom:16px;">Bridges receive signals from physical remotes and forward them to Home Assistant.</p>
      
      ${bridges.length === 0 ? `
        <div class="empty" style="padding:20px;">
          <ha-icon icon="mdi:router-wireless"></ha-icon>
          <h4>No Bridges Configured</h4>
          <p>Add a Pi Zero W USB bridge, ESP32 Bluetooth proxy, or Sonoff RF bridge.</p>
          <button class="btn btn-p" data-action="add-bridge" style="margin-top:12px;"><ha-icon icon="mdi:plus"></ha-icon> Add Bridge</button>
        </div>
      ` : `
        <div class="grid">
          ${bridges.map(b => `
            <div class="card ${b.online ? '' : 'offline'}">
              <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                <ha-icon icon="${bridgeTypeIcons[b.bridge_type] || 'mdi:router-wireless'}" style="color:${b.online ? '#4caf50' : '#888'};font-size:24px;"></ha-icon>
                <div style="flex:1;">
                  <div style="font-weight:600;">${b.name}</div>
                  <div style="color:#888;font-size:12px;">${b.bridge_type.replace(/_/g, ' ').toUpperCase()}</div>
                </div>
                <span class="status ${b.online ? 'online' : 'offline'}">${b.online ? 'Online' : 'Offline'}</span>
              </div>
              <div style="color:#888;font-size:13px;margin-bottom:8px;">
                ${b.room_name ? `<ha-icon icon="mdi:door" style="margin-right:4px;"></ha-icon>${b.room_name}` : '<span style="color:#666;">No room assigned</span>'}
              </div>
              ${b.host ? `<div style="color:#666;font-size:12px;">Host: ${b.host}${b.port ? ':' + b.port : ''}</div>` : ''}
              ${b.mqtt_topic ? `<div style="color:#666;font-size:12px;">MQTT: ${b.mqtt_topic}</div>` : ''}
              <div class="card-actions">
                <button class="btn btn-sm" data-action="edit-bridge" data-bridge-id="${b.id}">Edit</button>
                <button class="btn btn-sm btn-danger" data-action="delete-bridge" data-bridge-id="${b.id}">Delete</button>
              </div>
            </div>
          `).join('')}
        </div>
      `}
      
      <!-- Remotes Section -->
      <div class="section-header" style="margin-top:32px;">
        <h3><ha-icon icon="mdi:remote"></ha-icon> Configured Remotes</h3>
        <button class="btn btn-sm" data-action="add-remote"><ha-icon icon="mdi:plus"></ha-icon> Add Remote</button>
      </div>
      <p style="color:#888;margin-bottom:16px;">Physical remotes that can control your devices and scenes.</p>
      
      ${remotes.length === 0 ? `
        <div class="empty" style="padding:20px;">
          <ha-icon icon="mdi:remote"></ha-icon>
          <h4>No Remotes Configured</h4>
          <p>Add a Zigbee, RF 433MHz, Bluetooth, or USB remote.</p>
          <div style="display:flex;gap:8px;margin-top:16px;flex-wrap:wrap;justify-content:center;">
            <button class="btn" data-action="add-remote" data-type="zigbee"><ha-icon icon="mdi:zigbee"></ha-icon> Zigbee</button>
            <button class="btn" data-action="add-remote" data-type="rf_433"><ha-icon icon="mdi:access-point"></ha-icon> 433MHz RF</button>
            <button class="btn" data-action="add-remote" data-type="bluetooth"><ha-icon icon="mdi:bluetooth"></ha-icon> Bluetooth</button>
            <button class="btn" data-action="add-remote" data-type="usb_keyboard"><ha-icon icon="mdi:usb"></ha-icon> USB</button>
          </div>
        </div>
      ` : `
        <div class="grid">
          ${remotes.map(r => `
            <div class="card" data-remote-id="${r.id}">
              <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                <ha-icon icon="${remoteTypeIcons[r.remote_type] || 'mdi:remote'}" style="color:#03a9f4;font-size:24px;"></ha-icon>
                <div style="flex:1;">
                  <div style="font-weight:600;">${r.name}</div>
                  <div style="color:#888;font-size:12px;">${r.remote_type.replace(/_/g, ' ').toUpperCase()}${r.profile ? ' • ' + r.profile : ''}</div>
                </div>
                ${r.battery_level !== null ? `<span style="color:${r.battery_level > 20 ? '#4caf50' : '#f44336'};">${r.battery_level}%</span>` : ''}
              </div>
              <div style="color:#888;font-size:13px;margin-bottom:8px;">
                ${r.room_name ? `<ha-icon icon="mdi:door" style="margin-right:4px;"></ha-icon>${r.room_name}` : '<span style="color:#666;">No room assigned</span>'}
              </div>
              <div style="color:#666;font-size:12px;margin-bottom:8px;">
                ${Object.keys(r.button_mappings || {}).length} button(s) mapped
              </div>
              ${r.last_seen ? `<div style="color:#666;font-size:11px;">Last seen: ${new Date(r.last_seen).toLocaleString()}</div>` : ''}
              <div class="card-actions">
                <button class="btn btn-sm btn-p" data-action="map-buttons" data-remote-id="${r.id}">Map Buttons</button>
                <button class="btn btn-sm" data-action="edit-remote" data-remote-id="${r.id}">Edit</button>
                <button class="btn btn-sm btn-danger" data-action="delete-remote" data-remote-id="${r.id}">Delete</button>
              </div>
            </div>
          `).join('')}
        </div>
      `}
      
      <!-- Quick Setup Guide -->
      <div class="section-header" style="margin-top:32px;">
        <h3><ha-icon icon="mdi:help-circle"></ha-icon> Setup Guide</h3>
      </div>
      <div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">
        <div class="card" style="border-left:3px solid #4caf50;">
          <h4 style="color:#4caf50;margin:0 0 8px 0;"><ha-icon icon="mdi:zigbee"></ha-icon> Zigbee Remotes</h4>
          <p style="color:#888;font-size:13px;margin:0 0 12px 0;">IKEA TRADFRI, Aqara, Hue Dimmer, etc.</p>
          <ol style="color:#888;font-size:12px;margin:0;padding-left:16px;">
            <li>Pair remote with ZHA/Z2M/deCONZ</li>
            <li>Click "Discover" to find it</li>
            <li>Assign to room and map buttons</li>
          </ol>
        </div>
        <div class="card" style="border-left:3px solid #ff9800;">
          <h4 style="color:#ff9800;margin:0 0 8px 0;"><ha-icon icon="mdi:access-point"></ha-icon> 433MHz RF Remotes</h4>
          <p style="color:#888;font-size:13px;margin:0 0 12px 0;">Any 433MHz remote with Sonoff RF Bridge</p>
          <ol style="color:#888;font-size:12px;margin:0;padding-left:16px;">
            <li>Flash Sonoff RF Bridge with Tasmota</li>
            <li>Add bridge in OmniRemote</li>
            <li>Press remote buttons to learn codes</li>
          </ol>
        </div>
        <div class="card" style="border-left:3px solid #2196f3;">
          <h4 style="color:#2196f3;margin:0 0 8px 0;"><ha-icon icon="mdi:bluetooth"></ha-icon> Bluetooth Remotes</h4>
          <p style="color:#888;font-size:13px;margin:0 0 12px 0;">Media buttons, presenter remotes</p>
          <ol style="color:#888;font-size:12px;margin:0;padding-left:16px;">
            <li>Set up ESP32 Bluetooth Proxy</li>
            <li>Pair remote with ESP32</li>
            <li>Add in OmniRemote</li>
          </ol>
        </div>
        <div class="card" style="border-left:3px solid #9c27b0;">
          <h4 style="color:#9c27b0;margin:0 0 8px 0;"><ha-icon icon="mdi:usb"></ha-icon> USB Remotes (MX3, etc)</h4>
          <p style="color:#888;font-size:13px;margin:0 0 12px 0;">Air mouse remotes with USB dongle</p>
          <ol style="color:#888;font-size:12px;margin:0;padding-left:16px;">
            <li>Set up Pi Zero W with bridge script</li>
            <li>Plug USB dongle into Pi</li>
            <li>Bridge auto-discovers via MQTT</li>
          </ol>
        </div>
      </div>
    `;
  }

  _roomView() {
    const room = this._data.rooms.find(r => r.id === this._roomId);
    if (!room) return '<p>Room not found</p>';
    
    const devices = this._data.devices.filter(d => d.room_id === this._roomId);
    const scenes = this._data.scenes.filter(s => s.room_id === this._roomId);
    const physicalRemotes = (this._data.physicalRemotes || []).filter(r => r.room_id === this._roomId);
    
    // Get HA entities assigned to this room (by area or by our own assignment)
    const roomEntities = (this._data.haEntities || []).filter(e => 
      e.area_name === room.name || (room.entity_ids || []).includes(e.entity_id)
    );
    
    // Device type icons for HA entities
    const deviceTypeIcons = {
      // Covers
      'cover': 'mdi:window-shutter',
      'cover.blind': 'mdi:blinds',
      'cover.shade': 'mdi:roller-shade',
      'cover.curtain': 'mdi:curtains',
      'cover.garage': 'mdi:garage',
      'cover.awning': 'mdi:storefront-outline',
      'cover.shutter': 'mdi:window-shutter',
      // Media
      'media_player': 'mdi:cast',
      'media_player.tv': 'mdi:television',
      'media_player.speaker': 'mdi:speaker',
      'media_player.receiver': 'mdi:audio-video',
      // Lights
      'light': 'mdi:lightbulb',
      'light.ceiling': 'mdi:ceiling-light',
      // Climate
      'fan': 'mdi:fan',
      'climate': 'mdi:thermostat',
      // Switches
      'switch': 'mdi:toggle-switch',
      'switch.outlet': 'mdi:power-plug',
      // Remotes
      'remote': 'mdi:remote',
      // Locks
      'lock': 'mdi:lock',
      // Vacuum
      'vacuum': 'mdi:robot-vacuum',
    };
    
    const getEntityIcon = (entity) => {
      // Check for device_class specific icon
      if (entity.device_class) {
        const key = `${entity.domain}.${entity.device_class}`;
        if (deviceTypeIcons[key]) return deviceTypeIcons[key];
      }
      // Fall back to domain icon
      return deviceTypeIcons[entity.domain] || 'mdi:help-circle';
    };
    
    const getEntityStateColor = (entity) => {
      if (entity.state === 'on' || entity.state === 'open' || entity.state === 'playing') return '#4caf50';
      if (entity.state === 'off' || entity.state === 'closed' || entity.state === 'paused') return '#666';
      if (entity.state === 'unavailable') return '#f44336';
      return '#888';
    };
    
    return `
      <div class="page-header">
        <div style="display:flex;align-items:center;gap:12px;">
          <div style="width:48px;height:48px;background:#2a2a4a;border-radius:12px;display:flex;align-items:center;justify-content:center;">
            <ha-icon icon="${room.icon || 'mdi:sofa'}" style="font-size:28px;color:#64b5f6;"></ha-icon>
          </div>
          <div>
            <h2 style="margin:0;">${room.name}</h2>
            <div style="color:#888;font-size:13px;">${devices.length} devices • ${scenes.length} scenes • ${roomEntities.length} HA entities</div>
          </div>
        </div>
        <div style="display:flex;gap:8px;">
          <button class="btn btn-s" data-action="edit-room" data-room-id="${room.id}"><ha-icon icon="mdi:pencil"></ha-icon></button>
          <button class="btn btn-p" data-action="room-add-item" data-room-id="${room.id}"><ha-icon icon="mdi:plus"></ha-icon> Add</button>
        </div>
      </div>
      
      <!-- Scenes Section -->
      <div class="section-header" style="margin-top:24px;">
        <h3><ha-icon icon="mdi:play-box-multiple"></ha-icon> Scenes</h3>
        <button class="btn btn-sm" data-action="room-add-scene" data-room-id="${room.id}"><ha-icon icon="mdi:plus"></ha-icon></button>
      </div>
      ${scenes.length === 0 ? `
        <div class="card" style="text-align:center;padding:24px;color:#666;">
          <ha-icon icon="mdi:play-box-multiple-outline" style="font-size:32px;margin-bottom:8px;display:block;"></ha-icon>
          No scenes in this room
        </div>
      ` : `
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-bottom:24px;">
          ${scenes.map(s => `
            <div class="card" style="padding:12px;">
              <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                <div style="width:40px;height:40px;background:#2a2a4a;border-radius:8px;display:flex;align-items:center;justify-content:center;">
                  <ha-icon icon="${s.icon || 'mdi:play'}" style="font-size:20px;color:#64b5f6;"></ha-icon>
                </div>
                <div style="flex:1;min-width:0;">
                  <div style="font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${s.name}</div>
                  <div style="font-size:11px;color:#888;">${(s.on_actions || []).length} on / ${(s.off_actions || []).length} off</div>
                </div>
              </div>
              <div style="display:flex;gap:6px;">
                <button class="btn btn-sm btn-p" style="flex:1;" data-action="run-scene" data-scene-id="${s.id}">
                  <ha-icon icon="mdi:play"></ha-icon> ON
                </button>
                <button class="btn btn-sm" style="flex:1;" data-action="deactivate-scene" data-scene-id="${s.id}">
                  <ha-icon icon="mdi:stop"></ha-icon> OFF
                </button>
                <button class="btn btn-sm" data-action="edit-scene" data-scene-id="${s.id}">
                  <ha-icon icon="mdi:pencil"></ha-icon>
                </button>
              </div>
            </div>
          `).join('')}
        </div>
      `}
      
      <!-- Devices Section -->
      <div class="section-header">
        <h3><ha-icon icon="mdi:devices"></ha-icon> IR Devices</h3>
        <button class="btn btn-sm" data-action="room-add-device" data-room-id="${room.id}"><ha-icon icon="mdi:plus"></ha-icon></button>
      </div>
      ${devices.length === 0 ? `
        <div class="card" style="text-align:center;padding:24px;color:#666;">
          <ha-icon icon="mdi:remote-off" style="font-size:32px;margin-bottom:8px;display:block;"></ha-icon>
          No IR devices in this room
        </div>
      ` : `
        <div class="grid" style="margin-bottom:24px;">
          ${devices.map(d => `
            <div class="card">
              <div class="card-head">
                <div class="card-icon"><ha-icon icon="${this._catIcon(d.category)}"></ha-icon></div>
                <div class="card-info">
                  <div class="card-title">${d.name}</div>
                  <div class="card-sub">${d.brand || d.category || ''} • ${Object.keys(d.commands || {}).length} commands</div>
                </div>
              </div>
              <div class="card-btns">
                <button class="btn btn-s" data-action="open-device" data-device-id="${d.id}">Control</button>
                <button class="btn btn-sm" data-action="quick-power" data-device-id="${d.id}"><ha-icon icon="mdi:power"></ha-icon></button>
              </div>
            </div>
          `).join('')}
        </div>
      `}
      
      <!-- HA Entities Section -->
      <div class="section-header">
        <h3><ha-icon icon="mdi:home-assistant"></ha-icon> Home Assistant Entities</h3>
        <button class="btn btn-sm" data-action="room-add-entity" data-room-id="${room.id}"><ha-icon icon="mdi:plus"></ha-icon></button>
      </div>
      ${roomEntities.length === 0 ? `
        <div class="card" style="text-align:center;padding:24px;color:#666;">
          <ha-icon icon="mdi:home-assistant" style="font-size:32px;margin-bottom:8px;display:block;opacity:0.5;"></ha-icon>
          No HA entities assigned to this room
          <div style="margin-top:12px;">
            <button class="btn btn-sm" data-action="room-add-entity" data-room-id="${room.id}">
              <ha-icon icon="mdi:plus"></ha-icon> Add HA Entity
            </button>
          </div>
        </div>
      ` : `
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-bottom:24px;">
          ${roomEntities.map(e => `
            <div class="card" style="padding:12px;">
              <div style="display:flex;align-items:center;gap:12px;">
                <div style="width:40px;height:40px;background:#1b3d1b;border-radius:8px;display:flex;align-items:center;justify-content:center;">
                  <ha-icon icon="${getEntityIcon(e)}" style="font-size:20px;color:${getEntityStateColor(e)};"></ha-icon>
                </div>
                <div style="flex:1;min-width:0;">
                  <div style="font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${e.name}</div>
                  <div style="font-size:11px;color:#888;">
                    ${e.integration ? `<span style="background:#333;padding:2px 6px;border-radius:4px;margin-right:4px;">${e.integration}</span>` : ''}
                    ${e.state}
                    ${e.device_class ? ` • ${e.device_class}` : ''}
                  </div>
                </div>
                <div style="display:flex;gap:4px;">
                  ${this._getEntityQuickActions(e)}
                </div>
              </div>
              ${e.services && e.services.length > 0 ? `
                <div style="margin-top:8px;padding-top:8px;border-top:1px solid #333;">
                  <div style="font-size:11px;color:#666;margin-bottom:4px;">Available actions:</div>
                  <div style="display:flex;flex-wrap:wrap;gap:4px;">
                    ${e.services.slice(0, 6).map(svc => `
                      <button class="btn btn-sm" data-action="call-ha-service" data-entity-id="${e.entity_id}" data-service="${e.domain}.${svc}" style="font-size:10px;padding:4px 8px;">
                        ${svc.replace(/_/g, ' ')}
                      </button>
                    `).join('')}
                    ${e.services.length > 6 ? `<span style="font-size:10px;color:#666;">+${e.services.length - 6} more</span>` : ''}
                  </div>
                </div>
              ` : ''}
            </div>
          `).join('')}
        </div>
      `}
      
      <!-- Physical Remotes Section (if any) -->
      ${physicalRemotes.length > 0 ? `
        <div class="section-header">
          <h3><ha-icon icon="mdi:remote"></ha-icon> Physical Remotes</h3>
        </div>
        <div class="grid">
          ${physicalRemotes.map(r => `
            <div class="card">
              <div class="card-head">
                <div class="card-icon"><ha-icon icon="mdi:remote"></ha-icon></div>
                <div class="card-info">
                  <div class="card-title">${r.name}</div>
                  <div class="card-sub">${r.type || 'Unknown type'}</div>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      ` : ''}
    `;
  }
  
  _getEntityQuickActions(entity) {
    const domain = entity.domain;
    const state = entity.state;
    
    // Generate quick action buttons based on domain
    switch (domain) {
      case 'light':
      case 'switch':
      case 'input_boolean':
      case 'fan':
        return `
          <button class="btn btn-sm ${state === 'on' ? 'btn-p' : ''}" 
                  data-action="call-ha-service" data-entity-id="${entity.entity_id}" 
                  data-service="${domain}.toggle" title="Toggle">
            <ha-icon icon="mdi:power"></ha-icon>
          </button>
        `;
      
      case 'cover':
        return `
          <button class="btn btn-sm" data-action="call-ha-service" data-entity-id="${entity.entity_id}" 
                  data-service="cover.open_cover" title="Open">
            <ha-icon icon="mdi:arrow-up"></ha-icon>
          </button>
          <button class="btn btn-sm" data-action="call-ha-service" data-entity-id="${entity.entity_id}" 
                  data-service="cover.stop_cover" title="Stop">
            <ha-icon icon="mdi:stop"></ha-icon>
          </button>
          <button class="btn btn-sm" data-action="call-ha-service" data-entity-id="${entity.entity_id}" 
                  data-service="cover.close_cover" title="Close">
            <ha-icon icon="mdi:arrow-down"></ha-icon>
          </button>
        `;
      
      case 'media_player':
        return `
          <button class="btn btn-sm" data-action="call-ha-service" data-entity-id="${entity.entity_id}" 
                  data-service="media_player.toggle" title="Power">
            <ha-icon icon="mdi:power"></ha-icon>
          </button>
          <button class="btn btn-sm" data-action="call-ha-service" data-entity-id="${entity.entity_id}" 
                  data-service="media_player.volume_down" title="Vol-">
            <ha-icon icon="mdi:volume-minus"></ha-icon>
          </button>
          <button class="btn btn-sm" data-action="call-ha-service" data-entity-id="${entity.entity_id}" 
                  data-service="media_player.volume_up" title="Vol+">
            <ha-icon icon="mdi:volume-plus"></ha-icon>
          </button>
        `;
      
      case 'lock':
        return `
          <button class="btn btn-sm ${state === 'locked' ? 'btn-p' : ''}" 
                  data-action="call-ha-service" data-entity-id="${entity.entity_id}" 
                  data-service="lock.${state === 'locked' ? 'unlock' : 'lock'}" title="${state === 'locked' ? 'Unlock' : 'Lock'}">
            <ha-icon icon="mdi:${state === 'locked' ? 'lock' : 'lock-open'}"></ha-icon>
          </button>
        `;
      
      case 'climate':
        return `
          <button class="btn btn-sm ${state !== 'off' ? 'btn-p' : ''}" 
                  data-action="call-ha-service" data-entity-id="${entity.entity_id}" 
                  data-service="climate.turn_${state === 'off' ? 'on' : 'off'}" title="Toggle">
            <ha-icon icon="mdi:power"></ha-icon>
          </button>
        `;
      
      case 'scene':
      case 'script':
        return `
          <button class="btn btn-sm btn-p" data-action="call-ha-service" data-entity-id="${entity.entity_id}" 
                  data-service="${domain}.turn_on" title="Activate">
            <ha-icon icon="mdi:play"></ha-icon>
          </button>
        `;
      
      default:
        return '';
    }
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

  async _showImportHaEntityModal() {
    // Get HA entities with integration info
    const domains = ['media_player', 'light', 'switch', 'fan', 'climate', 'cover', 'remote', 'sensor', 'binary_sensor', 'button', 'scene'];
    const entities = [];
    const integrations = new Set();
    
    // Try to get entity registry for integration info
    let entityRegistry = {};
    let deviceRegistry = {};
    
    try {
      // Fetch entity registry
      const entityRegResult = await this._hass.callWS({ type: 'config/entity_registry/list' });
      if (entityRegResult) {
        entityRegResult.forEach(e => {
          entityRegistry[e.entity_id] = e;
        });
      }
      
      // Fetch device registry
      const deviceRegResult = await this._hass.callWS({ type: 'config/device_registry/list' });
      if (deviceRegResult) {
        deviceRegResult.forEach(d => {
          deviceRegistry[d.id] = d;
        });
      }
    } catch (e) {
      console.log('[OmniRemote] Could not fetch registries:', e);
    }
    
    if (this._hass && this._hass.states) {
      for (const entityId of Object.keys(this._hass.states)) {
        const domain = entityId.split('.')[0];
        if (domains.includes(domain)) {
          const state = this._hass.states[entityId];
          const regEntry = entityRegistry[entityId] || {};
          const deviceId = regEntry.device_id;
          const device = deviceId ? deviceRegistry[deviceId] : null;
          
          // Get integration name from platform or device
          let integration = regEntry.platform || '';
          if (!integration && device && device.identifiers && device.identifiers.length > 0) {
            integration = device.identifiers[0][0] || '';
          }
          if (!integration) {
            // Fallback: try to parse from entity_id
            const parts = entityId.split('.');
            if (parts.length > 1 && parts[1].includes('_')) {
              // e.g., media_player.onkyo_tx_nr838 -> onkyo
              const possibleInt = parts[1].split('_')[0];
              if (possibleInt.length > 2) integration = possibleInt;
            }
          }
          
          if (integration) {
            integrations.add(integration);
          }
          
          entities.push({
            entity_id: entityId,
            name: state.attributes.friendly_name || entityId,
            domain: domain,
            icon: state.attributes.icon || this._domainIcon(domain),
            integration: integration || 'unknown',
            device_name: device?.name || '',
            manufacturer: device?.manufacturer || '',
            model: device?.model || '',
          });
        }
      }
    }
    
    // Sort integrations
    const sortedIntegrations = Array.from(integrations).sort();
    
    // Group by domain
    const byDomain = {};
    entities.forEach(e => {
      if (!byDomain[e.domain]) byDomain[e.domain] = [];
      byDomain[e.domain].push(e);
    });
    
    this._haEntities = entities;
    this._haEntitiesByDomain = byDomain;
    this._haIntegrations = sortedIntegrations;
    
    this._modal = `
      <div class="modal-head">
        <h3><ha-icon icon="mdi:home-assistant"></ha-icon> Import from Home Assistant</h3>
        <button class="modal-close" data-action="close-modal">&times;</button>
      </div>
      <p style="color:#888;margin-top:0;">
        Import existing Home Assistant entities as OmniRemote devices for unified control.
      </p>
      
      <!-- Filter Controls -->
      <div style="display:flex;gap:12px;margin-bottom:16px;">
        <div class="fg" style="flex:1;margin:0;">
          <label class="fl">Search</label>
          <input type="text" class="fi" id="ha-entity-search" placeholder="Search name, entity, or integration...">
        </div>
        <div class="fg" style="flex:1;margin:0;">
          <label class="fl">Integration</label>
          <select class="fi" id="ha-integration-filter">
            <option value="">All Integrations (${sortedIntegrations.length})</option>
            ${sortedIntegrations.map(i => `<option value="${i}">${i} (${entities.filter(e => e.integration === i).length})</option>`).join('')}
          </select>
        </div>
        <div class="fg" style="flex:1;margin:0;">
          <label class="fl">Domain</label>
          <select class="fi" id="ha-domain-filter">
            <option value="">All Domains</option>
            ${Object.keys(byDomain).sort().map(d => `<option value="${d}">${d} (${byDomain[d].length})</option>`).join('')}
          </select>
        </div>
      </div>
      
      <!-- Entity List -->
      <div id="ha-entity-list" style="max-height:400px;overflow-y:auto;">
        ${this._renderHaEntityList(entities)}
      </div>
      
      <div style="margin-top:12px;padding-top:12px;border-top:1px solid #333;color:#888;font-size:12px;">
        Showing <span id="ha-entity-count">${entities.length}</span> of ${entities.length} entities
      </div>
    `;
    this._render();
    
    // Setup filter handlers
    setTimeout(() => {
      const searchInput = this.shadowRoot.getElementById('ha-entity-search');
      const integrationFilter = this.shadowRoot.getElementById('ha-integration-filter');
      const domainFilter = this.shadowRoot.getElementById('ha-domain-filter');
      
      const applyFilters = () => {
        const query = (searchInput?.value || '').toLowerCase();
        const integration = integrationFilter?.value || '';
        const domain = domainFilter?.value || '';
        
        let filtered = this._haEntities;
        
        if (integration) {
          filtered = filtered.filter(e => e.integration === integration);
        }
        if (domain) {
          filtered = filtered.filter(e => e.domain === domain);
        }
        if (query) {
          filtered = filtered.filter(e => 
            e.name.toLowerCase().includes(query) ||
            e.entity_id.toLowerCase().includes(query) ||
            e.integration.toLowerCase().includes(query) ||
            (e.manufacturer || '').toLowerCase().includes(query) ||
            (e.model || '').toLowerCase().includes(query)
          );
        }
        
        const listEl = this.shadowRoot.getElementById('ha-entity-list');
        const countEl = this.shadowRoot.getElementById('ha-entity-count');
        if (listEl) {
          listEl.innerHTML = this._renderHaEntityList(filtered);
          // Re-attach click handlers for import buttons
          this._attachImportHandlers(listEl);
        }
        if (countEl) {
          countEl.textContent = filtered.length;
        }
      };
      
      if (searchInput) searchInput.addEventListener('input', applyFilters);
      if (integrationFilter) integrationFilter.addEventListener('change', applyFilters);
      if (domainFilter) domainFilter.addEventListener('change', applyFilters);
      
      // Attach handlers for initial list
      const listEl = this.shadowRoot.getElementById('ha-entity-list');
      if (listEl) {
        this._attachImportHandlers(listEl);
      }
    }, 100);
  }
  
  _attachImportHandlers(container) {
    container.querySelectorAll('[data-action="import-ha-entity"]').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const entityId = btn.dataset.entityId;
        if (entityId) {
          await this._importHaEntity(entityId);
        }
      });
    });
  }
  
  _renderHaEntityList(entities) {
    if (entities.length === 0) {
      return `<div style="text-align:center;padding:40px;color:#666;">No entities match your filters</div>`;
    }
    
    // Group by integration for better organization
    const byIntegration = {};
    entities.forEach(e => {
      const key = e.integration || 'other';
      if (!byIntegration[key]) byIntegration[key] = [];
      byIntegration[key].push(e);
    });
    
    return Object.keys(byIntegration).sort().map(integration => `
      <div style="margin-bottom:16px;">
        <h4 style="margin:0 0 8px;color:#03a9f4;font-size:13px;text-transform:uppercase;display:flex;align-items:center;gap:8px;">
          <ha-icon icon="mdi:puzzle" style="font-size:14px;"></ha-icon> 
          ${integration}
          <span style="color:#666;font-size:11px;font-weight:normal;">(${byIntegration[integration].length})</span>
        </h4>
        <div style="display:flex;flex-direction:column;gap:4px;">
          ${byIntegration[integration].map(e => `
            <div class="ha-entity-row" style="display:flex;align-items:center;gap:12px;padding:10px;background:#1a1a2e;border-radius:6px;">
              <ha-icon icon="${e.icon}" style="color:#4caf50;font-size:20px;"></ha-icon>
              <div style="flex:1;min-width:0;">
                <div style="font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${e.name}</div>
                <div style="font-size:11px;color:#666;display:flex;gap:8px;flex-wrap:wrap;">
                  <span>${e.entity_id}</span>
                  ${e.manufacturer ? `<span>• ${e.manufacturer}</span>` : ''}
                  ${e.model ? `<span>• ${e.model}</span>` : ''}
                </div>
              </div>
              <span style="background:#333;padding:2px 8px;border-radius:4px;font-size:10px;color:#888;">${e.domain}</span>
              <button class="btn btn-sm btn-p" data-action="import-ha-entity" data-entity-id="${e.entity_id}">
                Import
              </button>
            </div>
          `).join('')}
        </div>
      </div>
    `).join('');
  }

  _domainIcon(domain) {
    const icons = {
      'media_player': 'mdi:cast',
      'light': 'mdi:lightbulb',
      'switch': 'mdi:toggle-switch',
      'fan': 'mdi:fan',
      'climate': 'mdi:thermostat',
      'cover': 'mdi:window-shutter',
      'remote': 'mdi:remote',
    };
    return icons[domain] || 'mdi:devices';
  }

  async _importHaEntity(entityId) {
    console.log('[OmniRemote] Import HA entity called:', entityId);
    
    if (!entityId) {
      console.error('[OmniRemote] No entityId provided');
      alert('Error: No entity ID provided');
      return;
    }
    
    const state = this._hass?.states?.[entityId];
    if (!state) {
      console.error('[OmniRemote] Entity not found in hass.states:', entityId);
      alert('Entity not found: ' + entityId);
      return;
    }
    
    const domain = entityId.split('.')[0];
    const name = state.attributes.friendly_name || entityId;
    
    console.log('[OmniRemote] Importing:', { entityId, name, domain });
    // Map domain to category
    const categoryMap = {
      'media_player': 'streaming',
      'light': 'light',
      'switch': 'other',
      'fan': 'fan',
      'climate': 'ac',
      'cover': 'other',
      'remote': 'other',
      'sensor': 'other',
      'binary_sensor': 'other',
      'button': 'other',
      'scene': 'other',
    };
    
    try {
      const payload = {
        name: name,
        category: categoryMap[domain] || 'other',
        entity_id: entityId,
        brand: 'Home Assistant',
        model: domain,
      };
      console.log('[OmniRemote] Sending import request:', payload);
      
      const res = await this._api('/api/omniremote/devices', 'POST', payload);
      console.log('[OmniRemote] Import response:', res);
      
      if (res.device) {
        alert(`Imported: ${name}`);
        this._modal = null;
        await this._loadData();
      } else {
        alert('Failed to import: ' + (res.error || 'Unknown error'));
      }
    } catch (err) {
      console.error('[OmniRemote] Import error:', err);
      alert('Import failed: ' + err.message);
    }
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
    
    // Common scene icons organized by category
    const iconCategories = {
      'Media': ['mdi:television', 'mdi:movie', 'mdi:music', 'mdi:speaker', 'mdi:gamepad-variant', 'mdi:youtube', 'mdi:netflix', 'mdi:play-circle', 'mdi:disc-player', 'mdi:radio'],
      'Lighting': ['mdi:lightbulb', 'mdi:lamp', 'mdi:ceiling-light', 'mdi:led-strip', 'mdi:brightness-7', 'mdi:weather-night', 'mdi:candle', 'mdi:spotlight-beam'],
      'Climate': ['mdi:thermometer', 'mdi:air-conditioner', 'mdi:fan', 'mdi:snowflake', 'mdi:fire', 'mdi:weather-sunny'],
      'Activities': ['mdi:sofa', 'mdi:bed', 'mdi:coffee', 'mdi:food', 'mdi:book-open-variant', 'mdi:dumbbell', 'mdi:meditation', 'mdi:party-popper'],
      'Security': ['mdi:shield-home', 'mdi:lock', 'mdi:cctv', 'mdi:alarm-light', 'mdi:motion-sensor', 'mdi:door-open'],
      'Power': ['mdi:power', 'mdi:power-plug', 'mdi:power-standby', 'mdi:flash', 'mdi:battery'],
      'Time': ['mdi:weather-sunset-up', 'mdi:weather-sunset-down', 'mdi:weather-night', 'mdi:clock-outline', 'mdi:alarm'],
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
            <div style="display:flex;gap:8px;align-items:center;">
              <div id="icon-preview" style="width:48px;height:48px;background:#2a2a4a;border-radius:8px;display:flex;align-items:center;justify-content:center;">
                <ha-icon icon="${this._editingScene.icon || 'mdi:television'}" style="font-size:28px;color:#64b5f6;"></ha-icon>
              </div>
              <input type="text" class="fi" id="scene-icon" value="${this._editingScene.icon || 'mdi:television'}" style="flex:1;">
              <button class="btn btn-sm" data-action="show-icon-picker" type="button">Browse</button>
            </div>
          </div>
        </div>
        
        <!-- Icon Picker (hidden by default) -->
        <div id="icon-picker" style="display:none;margin-bottom:16px;background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:12px;max-height:300px;overflow-y:auto;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <span style="font-weight:600;">Select Icon</span>
            <button class="btn btn-sm" data-action="close-icon-picker" type="button">&times; Close</button>
          </div>
          ${Object.entries(iconCategories).map(([category, icons]) => `
            <div style="margin-bottom:12px;">
              <div style="font-size:12px;color:#888;margin-bottom:6px;">${category}</div>
              <div style="display:flex;flex-wrap:wrap;gap:4px;">
                ${icons.map(icon => `
                  <button class="icon-pick-btn" data-action="pick-icon" data-icon="${icon}" type="button"
                          style="width:40px;height:40px;background:${this._editingScene.icon === icon ? '#3d5afe' : '#2a2a4a'};
                                 border:1px solid ${this._editingScene.icon === icon ? '#3d5afe' : '#444'};border-radius:6px;
                                 cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.15s;">
                    <ha-icon icon="${icon}" style="font-size:20px;color:${this._editingScene.icon === icon ? '#fff' : '#888'};"></ha-icon>
                  </button>
                `).join('')}
              </div>
            </div>
          `).join('')}
          <div style="margin-top:8px;padding-top:8px;border-top:1px solid #333;">
            <div style="font-size:12px;color:#888;margin-bottom:6px;">Custom (enter any mdi: icon)</div>
            <div style="display:flex;gap:8px;">
              <input type="text" class="fi" id="custom-icon-input" placeholder="mdi:your-icon" style="flex:1;">
              <button class="btn btn-sm btn-p" data-action="apply-custom-icon" type="button">Apply</button>
            </div>
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
    
    // Setup icon picker event listeners after render
    setTimeout(() => this._setupIconPicker(), 50);
  }
  
  _setupIconPicker() {
    const iconInput = this.shadowRoot.getElementById('scene-icon');
    const iconPreview = this.shadowRoot.getElementById('icon-preview');
    
    if (iconInput && iconPreview) {
      iconInput.addEventListener('input', (e) => {
        const icon = e.target.value || 'mdi:help';
        iconPreview.innerHTML = `<ha-icon icon="${icon}" style="font-size:28px;color:#64b5f6;"></ha-icon>`;
        if (this._editingScene) this._editingScene.icon = icon;
      });
    }
  }
  
  _toggleIconPicker(show) {
    const picker = this.shadowRoot.getElementById('icon-picker');
    if (picker) {
      picker.style.display = show ? 'block' : 'none';
    }
  }
  
  _selectIcon(icon) {
    const iconInput = this.shadowRoot.getElementById('scene-icon');
    const iconPreview = this.shadowRoot.getElementById('icon-preview');
    
    if (iconInput) iconInput.value = icon;
    if (iconPreview) {
      iconPreview.innerHTML = `<ha-icon icon="${icon}" style="font-size:28px;color:#64b5f6;"></ha-icon>`;
    }
    if (this._editingScene) this._editingScene.icon = icon;
    
    // Update button styles to show selection
    this.shadowRoot.querySelectorAll('.icon-pick-btn').forEach(btn => {
      const btnIcon = btn.dataset.icon;
      if (btnIcon === icon) {
        btn.style.background = '#3d5afe';
        btn.style.borderColor = '#3d5afe';
        btn.querySelector('ha-icon').style.color = '#fff';
      } else {
        btn.style.background = '#2a2a4a';
        btn.style.borderColor = '#444';
        btn.querySelector('ha-icon').style.color = '#888';
      }
    });
    
    // Close picker after selection
    this._toggleIconPicker(false);
  }
  
  _applyCustomIcon() {
    const customInput = this.shadowRoot.getElementById('custom-icon-input');
    if (customInput && customInput.value) {
      let icon = customInput.value.trim();
      if (!icon.startsWith('mdi:')) icon = 'mdi:' + icon;
      this._selectIcon(icon);
    }
  }

  // =============================================================================
  // Room Management
  // =============================================================================

  _showRoomAddItemModal(roomId) {
    const room = this._data.rooms.find(r => r.id === roomId);
    this._modal = `
      <div class="modal-head">
        <h3>Add to ${room?.name || 'Room'}</h3>
        <button class="modal-close" data-action="close-modal">&times;</button>
      </div>
      <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:16px;">
        <button class="btn btn-s" style="padding:24px;flex-direction:column;height:auto;" data-action="room-add-scene" data-room-id="${roomId}">
          <ha-icon icon="mdi:play-box-multiple" style="font-size:32px;margin-bottom:8px;"></ha-icon>
          <div style="font-weight:600;">New Scene</div>
          <div style="font-size:12px;color:#888;">Create automation sequence</div>
        </button>
        <button class="btn btn-s" style="padding:24px;flex-direction:column;height:auto;" data-action="room-add-device" data-room-id="${roomId}">
          <ha-icon icon="mdi:remote" style="font-size:32px;margin-bottom:8px;"></ha-icon>
          <div style="font-weight:600;">IR Device</div>
          <div style="font-size:12px;color:#888;">Add from catalog or manual</div>
        </button>
        <button class="btn btn-s" style="padding:24px;flex-direction:column;height:auto;" data-action="room-add-entity" data-room-id="${roomId}">
          <ha-icon icon="mdi:home-assistant" style="font-size:32px;margin-bottom:8px;color:#4caf50;"></ha-icon>
          <div style="font-weight:600;">HA Entity</div>
          <div style="font-size:12px;color:#888;">Import from Home Assistant</div>
        </button>
        <button class="btn btn-s" style="padding:24px;flex-direction:column;height:auto;" data-action="close-modal">
          <ha-icon icon="mdi:television" style="font-size:32px;margin-bottom:8px;"></ha-icon>
          <div style="font-weight:600;">Direct Channel</div>
          <div style="font-size:12px;color:#888;">Quick IR command button</div>
        </button>
      </div>
    `;
    this._render();
  }

  _showAddDeviceModal(roomId = null) {
    this._modal = `
      <div class="modal-head">
        <h3>Add Device</h3>
        <button class="modal-close" data-action="close-modal">&times;</button>
      </div>
      <p style="color:#888;">Choose how to add a device:</p>
      <div style="display:flex;flex-direction:column;gap:12px;">
        <button class="btn btn-s" style="justify-content:flex-start;padding:16px;" data-action="close-modal" onclick="setTimeout(() => { this.closest('omniremote-panel')._view = 'catalog'; this.closest('omniremote-panel')._render(); }, 100);">
          <ha-icon icon="mdi:book-open-variant" style="margin-right:12px;"></ha-icon>
          <div style="text-align:left;">
            <div style="font-weight:600;">From Catalog</div>
            <div style="font-size:12px;color:#888;">Browse pre-built device profiles</div>
          </div>
        </button>
        <button class="btn btn-s" style="justify-content:flex-start;padding:16px;" data-action="show-add-device-manual" data-room-id="${roomId || ''}">
          <ha-icon icon="mdi:pencil" style="margin-right:12px;"></ha-icon>
          <div style="text-align:left;">
            <div style="font-weight:600;">Manual Entry</div>
            <div style="font-size:12px;color:#888;">Create custom device with learned codes</div>
          </div>
        </button>
        <button class="btn btn-s" style="justify-content:flex-start;padding:16px;" data-action="show-import-flipper">
          <ha-icon icon="mdi:dolphin" style="margin-right:12px;"></ha-icon>
          <div style="text-align:left;">
            <div style="font-weight:600;">Import Flipper IR</div>
            <div style="font-size:12px;color:#888;">Import .ir file from Flipper Zero</div>
          </div>
        </button>
      </div>
    `;
    this._render();
  }

  _showEditRoomModal(roomId) {
    const room = this._data.rooms.find(r => r.id === roomId);
    if (!room) return;
    
    this._modal = `
      <div class="modal-head">
        <h3>Edit Room</h3>
        <button class="modal-close" data-action="close-modal">&times;</button>
      </div>
      <div class="fg">
        <label class="fl">Room Name</label>
        <input type="text" class="fi" id="edit-room-name" value="${room.name}">
      </div>
      <div class="fg">
        <label class="fl">Icon</label>
        <input type="text" class="fi" id="edit-room-icon" value="${room.icon || 'mdi:sofa'}">
      </div>
      <div style="display:flex;gap:8px;margin-top:16px;">
        <button class="btn btn-danger" data-action="delete-room" data-room-id="${roomId}">
          <ha-icon icon="mdi:delete"></ha-icon> Delete
        </button>
        <div style="flex:1;"></div>
        <button class="btn btn-s" data-action="close-modal">Cancel</button>
        <button class="btn btn-p" data-action="save-room-edit" data-room-id="${roomId}">Save</button>
      </div>
    `;
    this._render();
  }

  // =============================================================================
  // HA Entity Management
  // =============================================================================

  _showAddHAEntityModal(roomId) {
    const room = this._data.rooms.find(r => r.id === roomId);
    const entities = this._data.haEntities || [];
    
    // Get unique integrations/platforms
    const integrations = [...new Set(entities.map(e => e.integration || e.platform).filter(Boolean))].sort();
    
    // Get unique domains
    const domains = [...new Set(entities.map(e => e.domain))].sort();
    
    // Device type options for categorization
    const deviceTypes = [
      { value: 'projector_screen', label: 'Projector Screen', icon: 'mdi:projector-screen' },
      { value: 'tv', label: 'TV / Display', icon: 'mdi:television' },
      { value: 'receiver', label: 'Receiver / Amplifier', icon: 'mdi:audio-video' },
      { value: 'speaker', label: 'Speaker', icon: 'mdi:speaker' },
      { value: 'light', label: 'Light', icon: 'mdi:lightbulb' },
      { value: 'fan', label: 'Fan', icon: 'mdi:fan' },
      { value: 'blind', label: 'Blind / Shade', icon: 'mdi:blinds' },
      { value: 'garage', label: 'Garage Door', icon: 'mdi:garage' },
      { value: 'lock', label: 'Lock', icon: 'mdi:lock' },
      { value: 'thermostat', label: 'Thermostat', icon: 'mdi:thermostat' },
      { value: 'switch', label: 'Switch / Outlet', icon: 'mdi:toggle-switch' },
    ];
    
    this._haEntitySearch = { query: '', domain: '', integration: '' };
    this._selectedRoomId = roomId;
    
    this._modal = `
      <div class="modal-content" style="max-width:900px;max-height:85vh;">
        <div class="modal-head">
          <h3>Add HA Entity to ${room?.name || 'Room'}</h3>
          <button class="modal-close" data-action="close-modal">&times;</button>
        </div>
        
        <!-- Search/Filter Bar -->
        <div style="display:grid;grid-template-columns:1fr 150px 150px;gap:12px;margin-bottom:16px;">
          <div class="fg" style="margin:0;">
            <input type="text" class="fi" id="ha-entity-search" placeholder="Search by name, entity ID, or integration..." 
                   style="width:100%;" oninput="this.closest('omniremote-panel')._filterHAEntities()">
          </div>
          <div class="fg" style="margin:0;">
            <select class="fi" id="ha-entity-domain" onchange="this.closest('omniremote-panel')._filterHAEntities()">
              <option value="">All Domains</option>
              ${domains.map(d => `<option value="${d}">${d}</option>`).join('')}
            </select>
          </div>
          <div class="fg" style="margin:0;">
            <select class="fi" id="ha-entity-integration" onchange="this.closest('omniremote-panel')._filterHAEntities()">
              <option value="">All Integrations</option>
              ${integrations.map(i => `<option value="${i}">${i}</option>`).join('')}
            </select>
          </div>
        </div>
        
        <!-- Entity List -->
        <div id="ha-entity-list" style="max-height:400px;overflow-y:auto;border:1px solid #333;border-radius:8px;">
          ${this._renderHAEntityList(entities, roomId, deviceTypes)}
        </div>
        
        <div style="margin-top:16px;display:flex;justify-content:space-between;align-items:center;">
          <span style="color:#888;font-size:13px;">
            <ha-icon icon="mdi:information-outline" style="font-size:16px;"></ha-icon>
            Select entities to add to this room. You can assign a device type for better icons.
          </span>
          <button class="btn btn-s" data-action="close-modal">Done</button>
        </div>
      </div>
    `;
    this._render();
  }

  _renderHAEntityList(entities, roomId, deviceTypes) {
    const search = this._haEntitySearch?.query?.toLowerCase() || '';
    const domainFilter = this._haEntitySearch?.domain || '';
    const integrationFilter = this._haEntitySearch?.integration || '';
    
    const room = this._data.rooms.find(r => r.id === roomId);
    const roomEntityIds = room?.entity_ids || [];
    
    // Filter entities
    let filtered = entities.filter(e => {
      // Domain filter
      if (domainFilter && e.domain !== domainFilter) return false;
      
      // Integration filter
      if (integrationFilter && e.integration !== integrationFilter && e.platform !== integrationFilter) return false;
      
      // Search filter - match name, entity_id, integration, manufacturer, model
      if (search) {
        const searchFields = [
          e.name,
          e.entity_id,
          e.integration,
          e.platform,
          e.manufacturer,
          e.model,
          e.device_name,
        ].filter(Boolean).join(' ').toLowerCase();
        
        if (!searchFields.includes(search)) return false;
      }
      
      return true;
    });
    
    // Sort: already in room first, then by name
    filtered.sort((a, b) => {
      const aInRoom = roomEntityIds.includes(a.entity_id);
      const bInRoom = roomEntityIds.includes(b.entity_id);
      if (aInRoom && !bInRoom) return -1;
      if (!aInRoom && bInRoom) return 1;
      return a.name.localeCompare(b.name);
    });
    
    if (filtered.length === 0) {
      return `<div style="padding:32px;text-align:center;color:#888;">No entities match your search</div>`;
    }
    
    return filtered.slice(0, 50).map(e => {
      const inRoom = roomEntityIds.includes(e.entity_id);
      const deviceType = e.omni_device_type || e.device_class || '';
      
      return `
        <div style="display:flex;align-items:center;gap:12px;padding:12px;border-bottom:1px solid #333;
                    background:${inRoom ? '#1b3d1b' : 'transparent'};">
          <div style="width:40px;height:40px;background:#2a2a4a;border-radius:8px;display:flex;align-items:center;justify-content:center;">
            <ha-icon icon="${this._getEntityIconByDomain(e)}" style="font-size:20px;color:${inRoom ? '#4caf50' : '#888'};"></ha-icon>
          </div>
          <div style="flex:1;min-width:0;">
            <div style="font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${e.name}</div>
            <div style="font-size:11px;color:#888;">
              ${e.entity_id}
              ${e.integration ? ` • <span style="background:#333;padding:1px 5px;border-radius:3px;">${e.integration}</span>` : ''}
              ${e.manufacturer ? ` • ${e.manufacturer}` : ''}
            </div>
            ${e.services && e.services.length > 0 ? `
              <div style="font-size:10px;color:#666;margin-top:2px;">
                Services: ${e.services.slice(0, 4).join(', ')}${e.services.length > 4 ? '...' : ''}
              </div>
            ` : ''}
          </div>
          <div style="display:flex;gap:8px;align-items:center;">
            <select class="fi" style="width:140px;padding:6px;" 
                    data-entity-id="${e.entity_id}"
                    onchange="this.closest('omniremote-panel')._setEntityDeviceType('${e.entity_id}', this.value)">
              <option value="">Device Type...</option>
              <option value="projector_screen" ${deviceType === 'projector_screen' ? 'selected' : ''}>Projector Screen</option>
              <option value="tv" ${deviceType === 'tv' ? 'selected' : ''}>TV / Display</option>
              <option value="receiver" ${deviceType === 'receiver' ? 'selected' : ''}>Receiver</option>
              <option value="speaker" ${deviceType === 'speaker' ? 'selected' : ''}>Speaker</option>
              <option value="light" ${deviceType === 'light' ? 'selected' : ''}>Light</option>
              <option value="fan" ${deviceType === 'fan' ? 'selected' : ''}>Fan</option>
              <option value="blind" ${deviceType === 'blind' ? 'selected' : ''}>Blind/Shade</option>
              <option value="garage" ${deviceType === 'garage' ? 'selected' : ''}>Garage Door</option>
              <option value="lock" ${deviceType === 'lock' ? 'selected' : ''}>Lock</option>
              <option value="thermostat" ${deviceType === 'thermostat' ? 'selected' : ''}>Thermostat</option>
              <option value="switch" ${deviceType === 'switch' ? 'selected' : ''}>Switch/Outlet</option>
            </select>
            ${inRoom ? `
              <button class="btn btn-sm btn-danger" data-action="remove-entity-from-room" 
                      data-entity-id="${e.entity_id}" data-room-id="${roomId}">
                <ha-icon icon="mdi:minus"></ha-icon>
              </button>
            ` : `
              <button class="btn btn-sm btn-p" data-action="add-entity-to-room" 
                      data-entity-id="${e.entity_id}" data-room-id="${roomId}">
                <ha-icon icon="mdi:plus"></ha-icon>
              </button>
            `}
          </div>
        </div>
      `;
    }).join('') + (filtered.length > 50 ? `
      <div style="padding:12px;text-align:center;color:#888;font-size:13px;">
        Showing 50 of ${filtered.length} results. Use search to narrow down.
      </div>
    ` : '');
  }

  _getEntityIconByDomain(entity) {
    // Check for custom device type first
    const deviceType = entity.omni_device_type;
    if (deviceType) {
      const icons = {
        'projector_screen': 'mdi:projector-screen',
        'tv': 'mdi:television',
        'receiver': 'mdi:audio-video',
        'speaker': 'mdi:speaker',
        'light': 'mdi:lightbulb',
        'fan': 'mdi:fan',
        'blind': 'mdi:blinds',
        'garage': 'mdi:garage',
        'lock': 'mdi:lock',
        'thermostat': 'mdi:thermostat',
        'switch': 'mdi:toggle-switch',
      };
      if (icons[deviceType]) return icons[deviceType];
    }
    
    // Check device_class
    if (entity.device_class) {
      const classIcons = {
        'garage': 'mdi:garage',
        'blind': 'mdi:blinds',
        'shade': 'mdi:roller-shade',
        'curtain': 'mdi:curtains',
        'awning': 'mdi:storefront-outline',
        'shutter': 'mdi:window-shutter',
        'tv': 'mdi:television',
        'speaker': 'mdi:speaker',
        'receiver': 'mdi:audio-video',
      };
      if (classIcons[entity.device_class]) return classIcons[entity.device_class];
    }
    
    // Domain fallback
    const domainIcons = {
      'light': 'mdi:lightbulb',
      'switch': 'mdi:toggle-switch',
      'fan': 'mdi:fan',
      'cover': 'mdi:window-shutter',
      'climate': 'mdi:thermostat',
      'media_player': 'mdi:cast',
      'remote': 'mdi:remote',
      'lock': 'mdi:lock',
      'vacuum': 'mdi:robot-vacuum',
      'scene': 'mdi:palette',
      'script': 'mdi:script-text',
      'automation': 'mdi:robot',
      'input_boolean': 'mdi:toggle-switch-outline',
      'input_select': 'mdi:form-dropdown',
      'input_number': 'mdi:ray-vertex',
    };
    
    return domainIcons[entity.domain] || 'mdi:help-circle';
  }

  _filterHAEntities() {
    const searchInput = this.shadowRoot.getElementById('ha-entity-search');
    const domainSelect = this.shadowRoot.getElementById('ha-entity-domain');
    const integrationSelect = this.shadowRoot.getElementById('ha-entity-integration');
    const listDiv = this.shadowRoot.getElementById('ha-entity-list');
    
    this._haEntitySearch = {
      query: searchInput?.value || '',
      domain: domainSelect?.value || '',
      integration: integrationSelect?.value || '',
    };
    
    const deviceTypes = []; // We don't need to pass these for re-render
    if (listDiv) {
      listDiv.innerHTML = this._renderHAEntityList(
        this._data.haEntities || [],
        this._selectedRoomId,
        deviceTypes
      );
    }
  }

  async _addEntityToRoom(entityId, roomId) {
    const room = this._data.rooms.find(r => r.id === roomId);
    if (!room) return;
    
    // Initialize entity_ids array if needed
    if (!room.entity_ids) room.entity_ids = [];
    
    // Add if not already present
    if (!room.entity_ids.includes(entityId)) {
      room.entity_ids.push(entityId);
      
      // Save to backend
      await this._api('/api/omniremote/rooms', 'POST', {
        action: 'update',
        id: roomId,
        entity_ids: room.entity_ids,
      });
    }
    
    // Re-render the entity list
    this._filterHAEntities();
  }

  _setEntityDeviceType(entityId, deviceType) {
    // Store device type mapping locally
    if (!this._entityDeviceTypes) this._entityDeviceTypes = {};
    this._entityDeviceTypes[entityId] = deviceType;
    
    // Also update the entity in our data
    const entity = (this._data.haEntities || []).find(e => e.entity_id === entityId);
    if (entity) {
      entity.omni_device_type = deviceType;
    }
  }

  async _callHAService(entityId, service) {
    try {
      const [domain, serviceName] = service.split('.');
      
      await this.hass.callService(domain, serviceName, {
        entity_id: entityId,
      });
      
      // Refresh entity states after a short delay
      setTimeout(() => this._loadData(), 500);
      
    } catch (err) {
      console.error('Error calling HA service:', err);
      alert(`Failed to call ${service}: ${err.message}`);
    }
  }

  async _sendQuickPower(deviceId) {
    const device = this._data.devices.find(d => d.id === deviceId);
    if (!device) return;
    
    // Try to find a power command
    const powerCommands = ['power', 'power_toggle', 'Power', 'POWER', 'power_on'];
    const cmdName = powerCommands.find(c => device.commands && device.commands[c]);
    
    if (cmdName) {
      await this._sendCommand(deviceId, cmdName);
    } else {
      alert('No power command found for this device');
    }
  }

  async _removeEntityFromRoom(entityId, roomId) {
    const room = this._data.rooms.find(r => r.id === roomId);
    if (!room) return;
    
    // Remove from entity_ids array
    room.entity_ids = (room.entity_ids || []).filter(id => id !== entityId);
    
    // Save to backend
    await this._api('/api/omniremote/rooms', 'POST', {
      action: 'update',
      id: roomId,
      entity_ids: room.entity_ids,
    });
    
    // Re-render the entity list
    this._filterHAEntities();
  }

  async _deleteRoom(roomId) {
    if (!confirm('Delete this room? Devices will not be deleted but will no longer be assigned to this room.')) {
      return;
    }
    
    await this._api('/api/omniremote/rooms', 'POST', {
      action: 'delete',
      id: roomId,
    });
    
    // Navigate back to dashboard
    this._view = 'dashboard';
    this._modal = null;
    await this._loadData();
  }

  async _saveRoomEdit(roomId) {
    const nameInput = this.shadowRoot.getElementById('edit-room-name');
    const iconInput = this.shadowRoot.getElementById('edit-room-icon');
    
    await this._api('/api/omniremote/rooms', 'POST', {
      action: 'update',
      id: roomId,
      name: nameInput?.value || 'Room',
      icon: iconInput?.value || 'mdi:sofa',
    });
    
    this._modal = null;
    await this._loadData();
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
    
    console.log('[OmniRemote] Saving scene:', { sceneId, name, roomId, blasterId });
    
    if (!name) {
      alert('Please enter a scene name');
      return;
    }
    
    const sceneData = {
      name,
      icon,
      room_id: roomId === '' ? null : roomId,  // Ensure empty string becomes null
      blaster_id: blasterId === '' ? null : blasterId,
      on_actions: this._editingScene.on_actions,
      off_actions: this._editingScene.off_actions,
      controlled_device_ids: this._editingScene.on_actions
        .filter(a => a.action_type === 'ir_command' && a.device_id)
        .map(a => a.device_id),
      controlled_entity_ids: this._editingScene.on_actions
        .filter(a => a.action_type === 'ha_service' && a.entity_id)
        .map(a => a.entity_id),
    };
    
    console.log('[OmniRemote] Scene data:', sceneData);
    
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

  // ==========================================================================
  // Physical Remotes Management
  // ==========================================================================

  _showAddRemoteModal(remoteType = null) {
    const rooms = this._data.rooms || [];
    const bridges = this._data.remoteBridges || [];
    const profiles = this._data.remoteProfiles || [];
    
    // Filter profiles by type if specified
    const filteredProfiles = remoteType 
      ? profiles.filter(p => p.type === remoteType || p.type === remoteType.replace('_', ''))
      : profiles;
    
    this._editingRemote = null;
    
    this._modal = `
      <div class="modal-content" style="max-width:500px;">
        <h3><ha-icon icon="mdi:remote"></ha-icon> Add Physical Remote</h3>
        
        <div class="fg">
          <label class="fl">Remote Type</label>
          <select class="fi" id="remote-type">
            <option value="zigbee" ${remoteType === 'zigbee' ? 'selected' : ''}>Zigbee (IKEA, Aqara, Hue)</option>
            <option value="rf_433" ${remoteType === 'rf_433' ? 'selected' : ''}>433MHz RF (Sonoff Bridge)</option>
            <option value="bluetooth_ha" ${remoteType === 'bluetooth_ha' ? 'selected' : ''}>Bluetooth (HA Yellow / Built-in)</option>
            <option value="bluetooth" ${remoteType === 'bluetooth' ? 'selected' : ''}>Bluetooth (ESP32 Proxy)</option>
            <option value="usb_keyboard" ${remoteType === 'usb_keyboard' ? 'selected' : ''}>USB Keyboard (Pi Bridge)</option>
          </select>
        </div>
        
        <div class="fg">
          <label class="fl">Name</label>
          <input type="text" class="fi" id="remote-name" placeholder="Living Room Remote">
        </div>
        
        <div class="fg">
          <label class="fl">Room</label>
          <select class="fi" id="remote-room">
            <option value="">-- No Room --</option>
            ${rooms.map(r => `<option value="${r.id}">${r.name}</option>`).join('')}
          </select>
        </div>
        
        <div class="fg" id="bridge-select-group" style="display:${['usb_keyboard', 'bluetooth'].includes(remoteType) ? 'block' : 'none'};">
          <label class="fl">Bridge/Proxy</label>
          <select class="fi" id="remote-bridge">
            <option value="">-- Select Bridge --</option>
            ${bridges.map(b => `<option value="${b.id}">${b.name} (${b.bridge_type})</option>`).join('')}
          </select>
        </div>
        
        <div class="fg" id="zigbee-ieee-group" style="display:${remoteType === 'zigbee' ? 'block' : 'none'};">
          <label class="fl">Zigbee IEEE Address</label>
          <input type="text" class="fi" id="remote-zigbee-ieee" placeholder="00:11:22:33:44:55:66:77">
          <small style="color:#888;">Find this in ZHA/deCONZ/Z2M device info</small>
        </div>
        
        <div class="fg" id="rf-code-group" style="display:${remoteType === 'rf_433' ? 'block' : 'none'};">
          <label class="fl">RF Code Prefix</label>
          <input type="text" class="fi" id="remote-rf-prefix" placeholder="A1B2C3">
          <small style="color:#888;">Common prefix of all RF codes from this remote</small>
        </div>
        
        <!-- HA Bluetooth Section (for Yellow/built-in) -->
        <div id="bt-ha-group" style="display:${remoteType === 'bluetooth_ha' ? 'block' : 'none'};">
          <div class="fg">
            <label class="fl">Bluetooth Adapter</label>
            <select class="fi" id="remote-bt-adapter">
              <option value="hci0">hci0 (Built-in / HA Yellow)</option>
              <option value="hci1">hci1 (USB Dongle)</option>
            </select>
          </div>
          <div style="margin:12px 0;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <button class="btn btn-s" data-action="bt-scan-start" id="bt-scan-btn">
              <ha-icon icon="mdi:bluetooth-searching"></ha-icon> Scan
            </button>
            <input type="text" class="fi" id="bt-device-search" placeholder="Search by name or MAC..." style="flex:1;min-width:150px;">
            <span id="bt-scan-status" style="color:#888;font-size:12px;"></span>
          </div>
          <div id="bt-discovered-list" style="max-height:200px;overflow-y:auto;background:#0d0d1a;border-radius:8px;margin-bottom:12px;">
            <div style="padding:20px;text-align:center;color:#666;">
              <ha-icon icon="mdi:bluetooth" style="font-size:32px;"></ha-icon>
              <p style="margin:8px 0 0;">Click "Scan" to find nearby Bluetooth devices</p>
            </div>
          </div>
          <div class="fg">
            <label class="fl">Or Enter MAC Address Manually</label>
            <input type="text" class="fi" id="remote-bt-mac-ha" placeholder="AA:BB:CC:DD:EE:FF">
          </div>
        </div>
        
        <!-- ESP32 Bluetooth Section -->
        <div class="fg" id="bt-mac-group" style="display:${remoteType === 'bluetooth' ? 'block' : 'none'};">
          <label class="fl">Bluetooth MAC Address</label>
          <input type="text" class="fi" id="remote-bt-mac" placeholder="AA:BB:CC:DD:EE:FF">
        </div>
        
        <div class="fg">
          <label class="fl">Profile (Pre-defined buttons)</label>
          <select class="fi" id="remote-profile">
            <option value="">-- Custom / Manual --</option>
            ${filteredProfiles.map(p => `<option value="${p.id}">${p.name} (${p.buttons?.length || 0} buttons)</option>`).join('')}
          </select>
        </div>
        
        <div style="margin-top:20px;display:flex;gap:8px;justify-content:flex-end;">
          <button class="btn btn-s" data-action="close-modal">Cancel</button>
          <button class="btn btn-p" data-action="save-remote"><ha-icon icon="mdi:check"></ha-icon> Add Remote</button>
        </div>
      </div>
    `;
    this._render();
    
    // Add event listener for type change
    setTimeout(() => {
      const typeSelect = this.shadowRoot.getElementById('remote-type');
      if (typeSelect) {
        typeSelect.addEventListener('change', () => {
          const type = typeSelect.value;
          const bridgeGroup = this.shadowRoot.getElementById('bridge-select-group');
          const zigbeeGroup = this.shadowRoot.getElementById('zigbee-ieee-group');
          const rfGroup = this.shadowRoot.getElementById('rf-code-group');
          const btGroup = this.shadowRoot.getElementById('bt-mac-group');
          const btHaGroup = this.shadowRoot.getElementById('bt-ha-group');
          
          if (bridgeGroup) bridgeGroup.style.display = ['usb_keyboard', 'bluetooth'].includes(type) ? 'block' : 'none';
          if (zigbeeGroup) zigbeeGroup.style.display = type === 'zigbee' ? 'block' : 'none';
          if (rfGroup) rfGroup.style.display = type === 'rf_433' ? 'block' : 'none';
          if (btGroup) btGroup.style.display = type === 'bluetooth' ? 'block' : 'none';
          if (btHaGroup) btHaGroup.style.display = type === 'bluetooth_ha' ? 'block' : 'none';
        });
      }
      
      // Add Bluetooth scan handler
      const scanBtn = this.shadowRoot.getElementById('bt-scan-btn');
      if (scanBtn) {
        scanBtn.addEventListener('click', async () => {
          await this._scanBluetoothDevices();
        });
      }
    }, 100);
  }
  
  async _scanBluetoothDevices() {
    const statusEl = this.shadowRoot.getElementById('bt-scan-status');
    const listEl = this.shadowRoot.getElementById('bt-discovered-list');
    const adapterEl = this.shadowRoot.getElementById('remote-bt-adapter');
    const adapter = adapterEl?.value || 'hci0';
    
    if (statusEl) statusEl.innerHTML = '<ha-icon icon="mdi:loading" class="spin"></ha-icon> Scanning...';
    if (listEl) listEl.innerHTML = '<div style="padding:20px;text-align:center;color:#888;">Scanning for Bluetooth devices...</div>';
    
    try {
      const res = await this._api('/api/omniremote/bluetooth', 'POST', {
        action: 'scan',
        adapter: adapter,
        duration: 10,
      });
      
      // Store devices for filtering
      this._btDiscoveredDevices = res.devices || [];
      
      if (res.success && res.devices && res.devices.length > 0) {
        if (statusEl) statusEl.textContent = `Found ${res.devices.length} devices`;
        this._renderBluetoothDeviceList(res.devices);
        
        // Add search handler
        const searchEl = this.shadowRoot.getElementById('bt-device-search');
        if (searchEl) {
          searchEl.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const filtered = this._btDiscoveredDevices.filter(d => 
              (d.name || '').toLowerCase().includes(query) ||
              (d.mac || '').toLowerCase().includes(query)
            );
            this._renderBluetoothDeviceList(filtered);
          });
        }
      } else {
        if (statusEl) statusEl.textContent = 'No devices found';
        if (listEl) {
          listEl.innerHTML = `
            <div style="padding:20px;text-align:center;color:#888;">
              <p style="margin:0;">No Bluetooth devices found.</p>
              <p style="margin:8px 0 0;font-size:12px;">Make sure your device is in pairing mode and nearby.</p>
            </div>
          `;
        }
      }
    } catch (err) {
      console.error('[OmniRemote] Bluetooth scan error:', err);
      if (statusEl) statusEl.textContent = 'Scan failed: ' + err.message;
    }
  }
  
  _renderBluetoothDeviceList(devices) {
    const listEl = this.shadowRoot.getElementById('bt-discovered-list');
    const statusEl = this.shadowRoot.getElementById('bt-scan-status');
    const adapterEl = this.shadowRoot.getElementById('remote-bt-adapter');
    const adapter = adapterEl?.value || 'hci0';
    
    if (!listEl) return;
    
    if (devices.length === 0) {
      listEl.innerHTML = `
        <div style="padding:20px;text-align:center;color:#888;">
          No devices match your search.
        </div>
      `;
      return;
    }
    
    listEl.innerHTML = devices.map((d, i) => `
      <div class="bt-device-row" style="display:flex;align-items:center;gap:12px;padding:10px;border-bottom:1px solid #333;">
        <ha-icon icon="${d.paired ? 'mdi:bluetooth-connect' : 'mdi:bluetooth'}" 
                 style="color:${d.paired ? '#4caf50' : '#2196f3'};font-size:20px;"></ha-icon>
        <div style="flex:1;min-width:0;">
          <div style="font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${d.name || 'Unknown Device'}</div>
          <div style="font-size:11px;color:#888;font-family:monospace;">${d.mac}${d.rssi ? ' • ' + d.rssi + ' dBm' : ''}</div>
        </div>
        <button class="btn btn-sm btn-p bt-select-btn" id="bt-select-${i}" data-index="${i}">
          ${d.paired ? 'Select' : 'Pair'}
        </button>
      </div>
    `).join('');
    
    // Attach click handlers
    setTimeout(() => {
      devices.forEach((d, i) => {
        const btn = this.shadowRoot.getElementById(`bt-select-${i}`);
        if (btn) {
          btn.onclick = async () => {
            const macInput = this.shadowRoot.getElementById('remote-bt-mac-ha');
            const nameInput = this.shadowRoot.getElementById('remote-name');
            if (macInput) macInput.value = d.mac;
            if (nameInput && !nameInput.value) nameInput.value = d.name || 'Bluetooth Remote';
            
            // Try to pair if not already paired
            if (!d.paired) {
              btn.disabled = true;
              btn.innerHTML = '<ha-icon icon="mdi:loading" class="spin"></ha-icon>';
              if (statusEl) statusEl.innerHTML = '<ha-icon icon="mdi:loading" class="spin"></ha-icon> Pairing...';
              
              try {
                const pairRes = await this._api('/api/omniremote/bluetooth', 'POST', {
                  action: 'pair',
                  adapter: adapter,
                  mac: d.mac,
                });
                if (pairRes.success) {
                  btn.innerHTML = '✓ Paired';
                  btn.style.background = '#4caf50';
                  if (statusEl) statusEl.textContent = 'Paired: ' + (d.name || d.mac);
                  d.paired = true;
                } else {
                  btn.innerHTML = 'Retry';
                  btn.disabled = false;
                  if (statusEl) statusEl.textContent = 'Failed: ' + (pairRes.error || 'Unknown error');
                }
              } catch (err) {
                btn.innerHTML = 'Error';
                btn.disabled = false;
                if (statusEl) statusEl.textContent = 'Error: ' + err.message;
              }
            } else {
              if (statusEl) statusEl.textContent = 'Selected: ' + (d.name || d.mac);
            }
          };
        }
      });
    }, 50);
  }

  _showEditRemoteModal(remoteId) {
    const remote = this._data.physicalRemotes.find(r => r.id === remoteId);
    if (!remote) return;
    
    const rooms = this._data.rooms || [];
    const bridges = this._data.remoteBridges || [];
    
    this._editingRemote = remote;
    
    this._modal = `
      <div class="modal-content" style="max-width:500px;">
        <h3><ha-icon icon="mdi:remote"></ha-icon> Edit Remote</h3>
        
        <div class="fg">
          <label class="fl">Name</label>
          <input type="text" class="fi" id="remote-name" value="${remote.name || ''}">
        </div>
        
        <div class="fg">
          <label class="fl">Room</label>
          <select class="fi" id="remote-room">
            <option value="">-- No Room --</option>
            ${rooms.map(r => `<option value="${r.id}" ${remote.room_id === r.id ? 'selected' : ''}>${r.name}</option>`).join('')}
          </select>
        </div>
        
        <div class="fg">
          <label class="fl">Bridge</label>
          <select class="fi" id="remote-bridge">
            <option value="">-- No Bridge --</option>
            ${bridges.map(b => `<option value="${b.id}" ${remote.bridge_id === b.id ? 'selected' : ''}>${b.name}</option>`).join('')}
          </select>
        </div>
        
        <div class="fg">
          <label class="fl">Type</label>
          <input type="text" class="fi" value="${remote.remote_type}" disabled>
        </div>
        
        <div style="margin-top:20px;display:flex;gap:8px;justify-content:flex-end;">
          <button class="btn btn-s" data-action="close-modal">Cancel</button>
          <button class="btn btn-p" data-action="save-remote"><ha-icon icon="mdi:check"></ha-icon> Save</button>
        </div>
      </div>
    `;
    this._render();
  }

  async _saveRemote() {
    const name = this.shadowRoot.getElementById('remote-name')?.value;
    const roomId = this.shadowRoot.getElementById('remote-room')?.value;
    const bridgeId = this.shadowRoot.getElementById('remote-bridge')?.value;
    const remoteType = this.shadowRoot.getElementById('remote-type')?.value;
    const profile = this.shadowRoot.getElementById('remote-profile')?.value;
    const zigbeeIeee = this.shadowRoot.getElementById('remote-zigbee-ieee')?.value;
    const rfPrefix = this.shadowRoot.getElementById('remote-rf-prefix')?.value;
    const btMac = this.shadowRoot.getElementById('remote-bt-mac')?.value;
    
    if (!name) {
      alert('Please enter a name for the remote');
      return;
    }
    
    const data = {
      action: this._editingRemote ? 'update' : 'add',
      id: this._editingRemote?.id,
      name,
      room_id: roomId || null,
      bridge_id: bridgeId || null,
      remote_type: remoteType || this._editingRemote?.remote_type,
      profile: profile || null,
      zigbee_ieee: zigbeeIeee || null,
      rf_code_prefix: rfPrefix || null,
      bt_mac: btMac || null,
    };
    
    const res = await this._api('/api/omniremote/physical_remotes', 'POST', data);
    
    if (res.success) {
      this._modal = null;
      this._editingRemote = null;
      await this._loadData();
      this._render();
    } else {
      alert('Failed to save remote: ' + (res.error || 'Unknown error'));
    }
  }

  async _deleteRemote(remoteId) {
    if (!confirm('Delete this remote?')) return;
    
    const res = await this._api('/api/omniremote/physical_remotes', 'POST', {
      action: 'delete',
      id: remoteId
    });
    
    if (res.success) {
      await this._loadData();
      this._render();
    } else {
      alert('Failed to delete: ' + (res.error || 'Unknown error'));
    }
  }

  async _discoverRemotes() {
    const res = await this._api('/api/omniremote/physical_remotes', 'POST', {
      action: 'discover_zigbee'
    });
    
    if (res.discovered && res.discovered.length > 0) {
      const list = res.discovered.map(d => `• ${d.name} (${d.model || d.manufacturer || 'unknown'})`).join('\\n');
      alert('Found Zigbee remotes:\\n' + list + '\\n\\nAdd them manually with their IEEE address.');
    } else {
      alert('No new Zigbee remotes found. Make sure they are paired with ZHA/deCONZ/Z2M first.');
    }
  }

  _showButtonMappingModal(remoteId) {
    const remote = this._data.physicalRemotes.find(r => r.id === remoteId);
    if (!remote) return;
    
    const rooms = this._data.rooms || [];
    const scenes = this._data.scenes || [];
    const devices = this._data.devices || [];
    const mappings = remote.button_mappings || {};
    
    // Get profile buttons if available
    const profile = this._data.remoteProfiles?.find(p => p.id === remote.profile);
    const buttons = profile?.buttons || Object.keys(mappings);
    
    const actionTypes = [
      { value: 'scene', label: 'Run Scene' },
      { value: 'ir_command', label: 'Send IR Command' },
      { value: 'volume_up', label: 'Volume Up (Room)' },
      { value: 'volume_down', label: 'Volume Down (Room)' },
      { value: 'mute', label: 'Mute (Room)' },
      { value: 'channel_up', label: 'Channel Up (Room)' },
      { value: 'channel_down', label: 'Channel Down (Room)' },
      { value: 'toggle_device', label: 'Toggle Device Power' },
      { value: 'ha_service', label: 'Call HA Service' },
    ];
    
    this._editingRemote = remote;
    this._buttonMappings = { ...mappings };
    
    this._modal = `
      <div class="modal-content" style="max-width:700px;max-height:80vh;overflow-y:auto;">
        <h3><ha-icon icon="mdi:gesture-tap-button"></ha-icon> Button Mapping - ${remote.name}</h3>
        <p style="color:#888;margin-top:0;">Assign actions to each button on your remote.</p>
        
        <table style="width:100%;border-collapse:collapse;margin-top:16px;">
          <thead>
            <tr style="background:#252545;">
              <th style="padding:8px;text-align:left;">Button</th>
              <th style="padding:8px;text-align:left;">Action Type</th>
              <th style="padding:8px;text-align:left;">Target</th>
            </tr>
          </thead>
          <tbody>
            ${buttons.map(btn => {
              const mapping = mappings[btn] || {};
              return `
                <tr style="border-bottom:1px solid #333;">
                  <td style="padding:8px;font-weight:600;">${btn}</td>
                  <td style="padding:8px;">
                    <select class="fi" style="margin:0;" data-button="${btn}" data-field="action_type">
                      ${actionTypes.map(t => `<option value="${t.value}" ${mapping.action_type === t.value ? 'selected' : ''}>${t.label}</option>`).join('')}
                    </select>
                  </td>
                  <td style="padding:8px;">
                    <select class="fi" style="margin:0;" data-button="${btn}" data-field="action_target">
                      <option value="">-- Select --</option>
                      ${mapping.action_type === 'scene' || !mapping.action_type ? 
                        scenes.map(s => `<option value="${s.id}" ${mapping.action_target === s.id ? 'selected' : ''}>${s.name}</option>`).join('') :
                        devices.map(d => `<option value="${d.id}" ${mapping.action_target === d.id ? 'selected' : ''}>${d.name}</option>`).join('')
                      }
                    </select>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
        
        ${buttons.length === 0 ? `
          <p style="color:#888;text-align:center;padding:20px;">
            No buttons defined. Select a profile or add a custom button.
          </p>
          <div class="fg">
            <label class="fl">Add Custom Button</label>
            <div style="display:flex;gap:8px;">
              <input type="text" class="fi" id="new-button-name" placeholder="Button name (e.g., KEY_POWER)">
              <button class="btn btn-s" id="add-button-btn">Add</button>
            </div>
          </div>
        ` : ''}
        
        <div style="margin-top:20px;display:flex;gap:8px;justify-content:flex-end;">
          <button class="btn btn-s" data-action="close-modal">Cancel</button>
          <button class="btn btn-p" data-action="save-button-mapping"><ha-icon icon="mdi:check"></ha-icon> Save Mappings</button>
        </div>
      </div>
    `;
    this._render();
  }

  async _saveButtonMapping() {
    const remote = this._editingRemote;
    if (!remote) return;
    
    // Collect all mappings from the modal
    const selects = this.shadowRoot.querySelectorAll('[data-button][data-field]');
    const mappings = {};
    
    selects.forEach(sel => {
      const btn = sel.dataset.button;
      const field = sel.dataset.field;
      
      if (!mappings[btn]) mappings[btn] = { button_id: btn };
      mappings[btn][field] = sel.value;
    });
    
    // Save each mapping
    for (const [btnId, mapping] of Object.entries(mappings)) {
      if (mapping.action_type && mapping.action_target) {
        await this._api('/api/omniremote/physical_remotes', 'POST', {
          action: 'map_button',
          remote_id: remote.id,
          button_id: btnId,
          action_type: mapping.action_type,
          action_target: mapping.action_target,
        });
      }
    }
    
    this._modal = null;
    this._editingRemote = null;
    await this._loadData();
    this._render();
  }

  // ==========================================================================
  // Bridge Management
  // ==========================================================================

  _showAddBridgeModal() {
    const rooms = this._data.rooms || [];
    
    this._editingBridge = null;
    
    this._modal = `
      <div class="modal-content" style="max-width:500px;">
        <h3><ha-icon icon="mdi:router-wireless"></ha-icon> Add Remote Bridge</h3>
        <p style="color:#888;margin-top:0;">Bridges receive signals from physical remotes and forward them to Home Assistant.</p>
        
        <div class="fg">
          <label class="fl">Bridge Type</label>
          <select class="fi" id="bridge-type">
            <option value="usb_bridge">USB Bridge (Pi Zero W)</option>
            <option value="bluetooth_proxy">Bluetooth Proxy (ESP32)</option>
            <option value="rf_tasmota">RF Bridge (Sonoff + Tasmota)</option>
            <option value="rf_esphome">RF Receiver (ESPHome)</option>
            <option value="zigbee_zha">ZHA Coordinator</option>
            <option value="zigbee_z2m">Zigbee2MQTT</option>
            <option value="zigbee_deconz">deCONZ</option>
          </select>
        </div>
        
        <div class="fg">
          <label class="fl">Name</label>
          <input type="text" class="fi" id="bridge-name" placeholder="Living Room Bridge">
        </div>
        
        <div class="fg">
          <label class="fl">Room</label>
          <select class="fi" id="bridge-room">
            <option value="">-- No Room --</option>
            ${rooms.map(r => `<option value="${r.id}">${r.name}</option>`).join('')}
          </select>
        </div>
        
        <div class="fg" id="bridge-host-group">
          <label class="fl">Host/IP (optional)</label>
          <input type="text" class="fi" id="bridge-host" placeholder="192.168.1.100 or hostname">
        </div>
        
        <div class="fg" id="bridge-mqtt-group">
          <label class="fl">MQTT Topic (for Tasmota/ESPHome)</label>
          <input type="text" class="fi" id="bridge-mqtt" placeholder="tele/rf_bridge/RESULT">
        </div>
        
        <div style="margin-top:20px;display:flex;gap:8px;justify-content:flex-end;">
          <button class="btn btn-s" data-action="close-modal">Cancel</button>
          <button class="btn btn-p" data-action="save-bridge"><ha-icon icon="mdi:check"></ha-icon> Add Bridge</button>
        </div>
      </div>
    `;
    this._render();
  }

  _showEditBridgeModal(bridgeId) {
    const bridge = this._data.remoteBridges.find(b => b.id === bridgeId);
    if (!bridge) return;
    
    const rooms = this._data.rooms || [];
    
    this._editingBridge = bridge;
    
    this._modal = `
      <div class="modal-content" style="max-width:500px;">
        <h3><ha-icon icon="mdi:router-wireless"></ha-icon> Edit Bridge</h3>
        
        <div class="fg">
          <label class="fl">Name</label>
          <input type="text" class="fi" id="bridge-name" value="${bridge.name || ''}">
        </div>
        
        <div class="fg">
          <label class="fl">Room</label>
          <select class="fi" id="bridge-room">
            <option value="">-- No Room --</option>
            ${rooms.map(r => `<option value="${r.id}" ${bridge.room_id === r.id ? 'selected' : ''}>${r.name}</option>`).join('')}
          </select>
        </div>
        
        <div class="fg">
          <label class="fl">Host/IP</label>
          <input type="text" class="fi" id="bridge-host" value="${bridge.host || ''}">
        </div>
        
        <div class="fg">
          <label class="fl">MQTT Topic</label>
          <input type="text" class="fi" id="bridge-mqtt" value="${bridge.mqtt_topic || ''}">
        </div>
        
        <div class="fg">
          <label class="fl">Type</label>
          <input type="text" class="fi" value="${bridge.bridge_type}" disabled>
        </div>
        
        <div style="margin-top:20px;display:flex;gap:8px;justify-content:flex-end;">
          <button class="btn btn-s" data-action="close-modal">Cancel</button>
          <button class="btn btn-p" data-action="save-bridge"><ha-icon icon="mdi:check"></ha-icon> Save</button>
        </div>
      </div>
    `;
    this._render();
  }

  async _saveBridge() {
    const name = this.shadowRoot.getElementById('bridge-name')?.value;
    const roomId = this.shadowRoot.getElementById('bridge-room')?.value;
    const host = this.shadowRoot.getElementById('bridge-host')?.value;
    const mqttTopic = this.shadowRoot.getElementById('bridge-mqtt')?.value;
    const bridgeType = this.shadowRoot.getElementById('bridge-type')?.value;
    
    if (!name) {
      alert('Please enter a name for the bridge');
      return;
    }
    
    const data = {
      action: this._editingBridge ? 'update' : 'add',
      id: this._editingBridge?.id,
      name,
      room_id: roomId || null,
      host: host || null,
      mqtt_topic: mqttTopic || null,
      bridge_type: bridgeType || this._editingBridge?.bridge_type,
    };
    
    const res = await this._api('/api/omniremote/remote_bridges', 'POST', data);
    
    if (res.success) {
      this._modal = null;
      this._editingBridge = null;
      await this._loadData();
      this._render();
    } else {
      alert('Failed to save bridge: ' + (res.error || 'Unknown error'));
    }
  }

  async _deleteBridge(bridgeId) {
    if (!confirm('Delete this bridge? Remotes using it will need to be reconfigured.')) return;
    
    const res = await this._api('/api/omniremote/remote_bridges', 'POST', {
      action: 'delete',
      id: bridgeId
    });
    
    if (res.success) {
      await this._loadData();
      this._render();
    } else {
      alert('Failed to delete: ' + (res.error || 'Unknown error'));
    }
  }

  // ==========================================================================
  // IR Debugger Functions
  // ==========================================================================

  async _refreshDebugLog() {
    const res = await this._api('/api/omniremote/debug');
    if (res.log) {
      this._debugLog = res.log;
      this._render();
    }
  }

  async _clearDebugLog() {
    const res = await this._api('/api/omniremote/debug', 'POST', { action: 'clear' });
    if (res.success) {
      this._debugLog = [];
      this._render();
    }
  }

  async _checkBlasterStatus() {
    const res = await this._api('/api/omniremote/debug', 'POST', { action: 'blaster_status' });
    
    if (res.blasters) {
      // Update status indicators in the UI
      res.blasters.forEach(b => {
        const card = this.shadowRoot.querySelector(`[data-blaster-id="${b.id}"]`);
        if (card) {
          const indicator = card.querySelector('.status-indicator');
          if (indicator) {
            indicator.style.background = b.connected ? '#4caf50' : '#f44336';
            indicator.title = b.connected ? 'Connected' : 'Disconnected';
          }
        }
      });
      
      const connected = res.blasters.filter(b => b.connected).length;
      alert(`Blaster Status: ${connected}/${res.total} connected`);
    }
  }

  async _testEncode() {
    const protocol = this.shadowRoot.getElementById('debug-protocol')?.value;
    const address = this.shadowRoot.getElementById('debug-address')?.value;
    const command = this.shadowRoot.getElementById('debug-command')?.value;
    
    const res = await this._api('/api/omniremote/debug', 'POST', {
      action: 'test_encode',
      protocol,
      address,
      command,
    });
    
    const resultDiv = this.shadowRoot.getElementById('encode-result');
    const outputDiv = this.shadowRoot.getElementById('encode-output');
    
    if (resultDiv && outputDiv) {
      resultDiv.style.display = 'block';
      
      if (res.success) {
        outputDiv.innerHTML = `
          <div style="color:#4caf50;margin-bottom:8px;">✓ Encoding successful</div>
          <div><strong>Protocol:</strong> ${res.protocol}</div>
          <div><strong>Address:</strong> 0x${res.address}</div>
          <div><strong>Command:</strong> 0x${res.command}</div>
          <div><strong>Packet size:</strong> ${res.broadlink_bytes} bytes</div>
          <div style="margin-top:8px;word-break:break-all;">
            <strong>Base64:</strong><br>
            <span style="color:#888;">${res.broadlink_base64}</span>
          </div>
          <div style="margin-top:8px;word-break:break-all;">
            <strong>Hex:</strong><br>
            <span style="color:#666;">${res.broadlink_hex}</span>
          </div>
        `;
      } else {
        outputDiv.innerHTML = `
          <div style="color:#f44336;">✗ Encoding failed</div>
          <div>${res.error || 'Unknown error'}</div>
        `;
      }
    }
    
    // Refresh log to show encoding details
    await this._refreshDebugLog();
  }

  async _quickTest(protocol, addr, cmd) {
    // Get selected blaster
    const blasterSelect = this.shadowRoot.getElementById('debug-blaster');
    const blasterId = blasterSelect?.value || this._debugBlaster || '';
    
    const res = await this._api('/api/omniremote/debug', 'POST', {
      action: 'test_encode',
      protocol,
      address: addr,
      command: cmd,
    });
    
    if (res.success && res.broadlink_base64) {
      // Try to send it via selected blaster
      const sendRes = await this._api('/api/omniremote/test', 'POST', {
        action: 'send_raw',
        broadlink_code: res.broadlink_base64,
        blaster_id: blasterId || undefined,
      });
      
      // Refresh log
      await this._refreshDebugLog();
      
      if (!sendRes.success) {
        alert('Send failed: ' + (sendRes.error || 'Unknown error'));
      }
    } else {
      alert('Encoding failed: ' + (res.error || 'Unknown error'));
    }
  }

  async _debugCatalogTest(deviceId, cmdName) {
    // Get selected blaster
    const blasterSelect = this.shadowRoot.getElementById('debug-blaster');
    const blasterId = blasterSelect?.value || this._debugBlaster || '';
    
    console.log('[OmniRemote] debugCatalogTest:', { deviceId, cmdName, blasterId });
    
    // Send the catalog command via the test API
    const res = await this._api('/api/omniremote/test', 'POST', {
      action: 'send_catalog_code',
      catalog_id: deviceId,
      command: cmdName,
      blaster_id: blasterId || undefined,
    });
    
    console.log('[OmniRemote] debugCatalogTest result:', res);
    
    // Refresh log
    await this._refreshDebugLog();
    
    if (!res.success) {
      alert('Send failed: ' + (res.error || 'Unknown error'));
    }
  }

  async _testSendDebug() {
    // Get selected blaster
    const blasterSelect = this.shadowRoot.getElementById('debug-blaster');
    const blasterId = blasterSelect?.value || this._debugBlaster || '';
    
    const protocol = this.shadowRoot.getElementById('debug-protocol')?.value || 'samsung32';
    const address = this.shadowRoot.getElementById('debug-address')?.value || '07';
    const command = this.shadowRoot.getElementById('debug-command')?.value || '02';
    
    // First encode
    const encRes = await this._api('/api/omniremote/debug', 'POST', {
      action: 'test_encode',
      protocol,
      address,
      command,
    });
    
    if (!encRes.success || !encRes.broadlink_base64) {
      alert('Encoding failed: ' + (encRes.error || 'Unknown error'));
      return;
    }
    
    // Show encoding result
    const resultDiv = this.shadowRoot.getElementById('encode-result');
    const outputDiv = this.shadowRoot.getElementById('encode-output');
    if (resultDiv && outputDiv) {
      resultDiv.style.display = 'block';
      outputDiv.innerHTML = `
        <div style="color:#4caf50;margin-bottom:8px;">✓ Encoded successfully</div>
        <div>Protocol: <span style="color:#64b5f6;">${protocol}</span></div>
        <div>Address: <span style="color:#64b5f6;">0x${address}</span></div>
        <div>Command: <span style="color:#64b5f6;">0x${command}</span></div>
        <div>Packet size: <span style="color:#64b5f6;">${encRes.byte_count || '?'} bytes</span></div>
        <div style="margin-top:8px;word-break:break-all;">Base64: <span style="color:#888;">${encRes.broadlink_base64.substring(0, 60)}...</span></div>
      `;
    }
    
    // Send via selected blaster
    const sendRes = await this._api('/api/omniremote/test', 'POST', {
      action: 'send_raw',
      broadlink_code: encRes.broadlink_base64,
      blaster_id: blasterId || undefined,
    });
    
    // Refresh log
    await this._refreshDebugLog();
    
    if (!sendRes.success) {
      alert('Send failed: ' + (sendRes.error || 'Unknown error'));
    }
  }

  // =============================================================================
  // Flipper Zero Methods
  // =============================================================================

  async _flipperDiscover(connectionType) {
    const statusDiv = this.shadowRoot.getElementById('flipper-discovered');
    const listDiv = this.shadowRoot.getElementById('flipper-discovered-list');
    
    if (statusDiv) statusDiv.style.display = 'block';
    if (listDiv) listDiv.innerHTML = '<p style="text-align:center;padding:16px;"><ha-icon icon="mdi:loading" class="spin"></ha-icon> Scanning for Flipper Zero devices...</p>';
    
    try {
      const res = await this._api('/api/omniremote/flipper', 'POST', {
        action: 'discover',
        connection_type: connectionType,
      });
      
      console.log('[OmniRemote] Flipper discover result:', res);
      
      if (res.devices && res.devices.length > 0) {
        if (listDiv) {
          listDiv.innerHTML = res.devices.map((d, i) => `
            <div class="flipper-device-row" style="display:flex;align-items:center;gap:12px;padding:12px;border-bottom:1px solid #333;">
              <ha-icon icon="${d.connection_type === 'bluetooth' ? 'mdi:bluetooth' : 'mdi:usb'}" 
                       style="font-size:24px;color:#2196f3;"></ha-icon>
              <div style="flex:1;">
                <div style="font-weight:600;">${d.name}</div>
                <div style="font-size:12px;color:#888;">${d.port} ${d.rssi ? '• RSSI: ' + d.rssi : ''}</div>
              </div>
              <button class="btn btn-sm btn-p" id="flipper-add-${i}"
                      style="min-width:80px;">
                <ha-icon icon="mdi:plus"></ha-icon> Add
              </button>
            </div>
          `).join('');
          
          // Attach click handlers after a brief delay to ensure DOM is ready
          setTimeout(() => {
            res.devices.forEach((d, i) => {
              const btn = this.shadowRoot.getElementById(`flipper-add-${i}`);
              if (btn) {
                console.log('[OmniRemote] Attaching click handler to flipper-add-' + i);
                btn.onclick = async (e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  
                  // Visual feedback
                  btn.disabled = true;
                  btn.innerHTML = '<ha-icon icon="mdi:loading" class="spin"></ha-icon> Adding...';
                  
                  const data = {
                    deviceId: d.id,
                    name: d.name,
                    connectionType: d.connection_type,
                    port: d.port,
                  };
                  console.log('[OmniRemote] Add button clicked for:', data);
                  await this._flipperAdd(data);
                };
              } else {
                console.error('[OmniRemote] Could not find button flipper-add-' + i);
              }
            });
          }, 50);
        }
      } else {
        if (listDiv) {
          listDiv.innerHTML = `
            <p style="text-align:center;padding:16px;color:#888;">
              No Flipper Zero devices found. Make sure your Flipper is:
              <br>• Powered on
              <br>• Connected via USB or Bluetooth enabled
              <br>• Not in use by another application
            </p>
          `;
        }
      }
    } catch (err) {
      console.error('[OmniRemote] Flipper discover error:', err);
      if (listDiv) {
        listDiv.innerHTML = `<p style="text-align:center;padding:16px;color:#f44336;">Error: ${err.message}</p>`;
      }
    }
  }

  async _flipperAdd(data) {
    console.log('[OmniRemote] Flipper add called with:', data);
    
    // Validate data
    if (!data.deviceId) {
      console.error('[OmniRemote] Missing deviceId in flipper-add');
      alert('Error: Missing device ID');
      return;
    }
    
    try {
      const res = await this._api('/api/omniremote/flipper', 'POST', {
        action: 'add',
        device_id: data.deviceId,
        name: data.name || 'Flipper Zero',
        connection_type: data.connectionType || 'usb',
        port: data.port || '',
      });
      
      console.log('[OmniRemote] Flipper add response:', res);
      
      if (res.success) {
        // Try to connect immediately
        await this._flipperConnect(data.deviceId);
        await this._loadFlipperDevices();
        this._modal = null;
        this._render();
        alert('Flipper Zero added successfully!');
      } else {
        alert('Failed to add Flipper: ' + (res.error || 'Unknown error'));
      }
    } catch (err) {
      console.error('[OmniRemote] Flipper add error:', err);
      alert('Error adding Flipper: ' + err.message);
    }
  }

  async _flipperConnect(deviceId) {
    const res = await this._api('/api/omniremote/flipper', 'POST', {
      action: 'connect',
      device_id: deviceId,
    });
    
    if (res.success) {
      await this._loadFlipperDevices();
      this._render();
    } else {
      alert('Failed to connect to Flipper: ' + (res.error || 'Unknown error'));
    }
  }

  async _flipperDisconnect(deviceId) {
    await this._api('/api/omniremote/flipper', 'POST', {
      action: 'disconnect',
      device_id: deviceId,
    });
    await this._loadFlipperDevices();
    this._render();
  }

  async _flipperRemove(deviceId) {
    if (!confirm('Remove this Flipper Zero?')) return;
    
    await this._api('/api/omniremote/flipper', 'POST', {
      action: 'remove',
      device_id: deviceId,
    });
    await this._loadFlipperDevices();
    this._render();
  }

  async _flipperTest(deviceId) {
    // Show test modal
    this._modal = `
      <div class="modal-head">
        <h3>Test Flipper IR</h3>
        <button class="modal-close" data-action="close-modal">&times;</button>
      </div>
      <p style="color:#888;">Send a test IR command via Flipper Zero.</p>
      <div class="fg">
        <label class="fl">Protocol</label>
        <select class="fi" id="flipper-protocol">
          <option value="Samsung32">Samsung32</option>
          <option value="NEC">NEC</option>
          <option value="SIRC">Sony SIRC</option>
          <option value="RC5">RC5</option>
          <option value="RC6">RC6</option>
        </select>
      </div>
      <div style="display:flex;gap:12px;">
        <div class="fg" style="flex:1;">
          <label class="fl">Address (hex)</label>
          <input type="text" class="fi" id="flipper-address" value="07" placeholder="07">
        </div>
        <div class="fg" style="flex:1;">
          <label class="fl">Command (hex)</label>
          <input type="text" class="fi" id="flipper-command" value="02" placeholder="02">
        </div>
      </div>
      <div style="margin-top:16px;text-align:right;">
        <button class="btn btn-p" id="flipper-send-btn" data-flipper-id="${deviceId}">
          <ha-icon icon="mdi:send"></ha-icon> Send IR
        </button>
      </div>
    `;
    this._render();
    
    // Add send handler
    setTimeout(() => {
      const sendBtn = this.shadowRoot.getElementById('flipper-send-btn');
      if (sendBtn) {
        sendBtn.addEventListener('click', async () => {
          const protocol = this.shadowRoot.getElementById('flipper-protocol').value;
          const address = this.shadowRoot.getElementById('flipper-address').value;
          const command = this.shadowRoot.getElementById('flipper-command').value;
          
          const res = await this._api('/api/omniremote/flipper', 'POST', {
            action: 'send_ir',
            device_id: deviceId,
            protocol,
            address,
            command,
          });
          
          if (res.success) {
            alert('IR command sent!');
          } else {
            alert('Failed: ' + (res.error || 'Unknown error'));
          }
        });
      }
    }, 100);
  }

  async _flipperShowFiles(deviceId) {
    const res = await this._api('/api/omniremote/flipper', 'POST', {
      action: 'list_files',
      device_id: deviceId,
    });
    
    if (res.success) {
      const files = res.files || [];
      this._modal = `
        <div class="modal-head">
          <h3>Flipper IR Files</h3>
          <button class="modal-close" data-action="close-modal">&times;</button>
        </div>
        <p style="color:#888;">IR files stored on Flipper Zero SD card.</p>
        ${files.length === 0 ? `
          <p style="text-align:center;color:#666;">No IR files found on SD card.</p>
        ` : `
          <div style="max-height:300px;overflow-y:auto;">
            ${files.map(f => `
              <div style="display:flex;justify-content:space-between;align-items:center;padding:8px;border-bottom:1px solid #333;">
                <span><ha-icon icon="mdi:file"></ha-icon> ${f}</span>
                <button class="btn btn-sm" data-action="flipper-import-file" data-flipper-id="${deviceId}" data-filename="${f}">
                  Import
                </button>
              </div>
            `).join('')}
          </div>
        `}
      `;
      this._render();
    } else {
      alert('Failed to list files: ' + (res.error || 'Unknown error'));
    }
  }

  async _loadFlipperDevices() {
    const res = await this._api('/api/omniremote/flipper', 'GET');
    this._data.flippers = res.devices || [];
  }

  // ===========================================
  // REMOTE PROFILE BUILDER
  // ===========================================

  _builderView() {
    if (this._builderProfileId) {
      return this._profileEditorView();
    }
    return this._profilesListView();
  }

  _profilesListView() {
    const profiles = this._data.remoteProfiles || [];
    const templates = [
      // Basic device templates
      { id: 'tv_basic', name: 'TV Remote', icon: 'mdi:television', device_type: 'tv', rows: 10, cols: 4, category: 'basic' },
      { id: 'receiver', name: 'AV Receiver', icon: 'mdi:speaker', device_type: 'receiver', rows: 12, cols: 4, category: 'basic' },
      { id: 'streaming', name: 'Streaming', icon: 'mdi:cast', device_type: 'streaming', rows: 8, cols: 3, category: 'basic' },
      { id: 'soundbar', name: 'Soundbar', icon: 'mdi:speaker-wireless', device_type: 'soundbar', rows: 6, cols: 3, category: 'basic' },
      { id: 'projector', name: 'Projector', icon: 'mdi:projector', device_type: 'projector', rows: 10, cols: 4, category: 'basic' },
      { id: 'ac', name: 'Air Conditioner', icon: 'mdi:air-conditioner', device_type: 'ac', rows: 8, cols: 4, category: 'basic' },
      { id: 'fan', name: 'Ceiling Fan', icon: 'mdi:ceiling-fan', device_type: 'fan', rows: 6, cols: 3, category: 'basic' },
      // Design variations
      { id: 'tv_blackout', name: 'TV Blackout', icon: 'mdi:television', device_type: 'tv', rows: 10, cols: 4, category: 'design', desc: 'Dark stealth' },
      { id: 'tv_backlit', name: 'TV Backlit', icon: 'mdi:led-strip-variant', device_type: 'tv', rows: 10, cols: 4, category: 'design', desc: 'Neon glow' },
      { id: 'minimal_circle', name: 'Minimal', icon: 'mdi:circle-outline', device_type: 'universal', rows: 8, cols: 3, category: 'design', desc: 'Clean circles' },
      { id: 'gaming', name: 'Gaming', icon: 'mdi:gamepad-variant', device_type: 'gaming', rows: 8, cols: 4, category: 'design', desc: 'Controller' },
      // Blank
      { id: 'universal', name: 'Blank Canvas', icon: 'mdi:remote', device_type: 'universal', rows: 8, cols: 4, category: 'blank' },
    ];
    
    const basicTemplates = templates.filter(t => t.category === 'basic');
    const designTemplates = templates.filter(t => t.category === 'design');
    const blankTemplates = templates.filter(t => t.category === 'blank');

    return `
      <div class="builder-container">
        <!-- Custom Profiles Section -->
        <div class="section-header">
          <h3><ha-icon icon="mdi:remote"></ha-icon> My Remote Profiles</h3>
          <span class="badge">${profiles.length}</span>
        </div>
        <p style="color:#888;margin-bottom:16px;">Custom remote layouts you've created. These sync to mobile apps.</p>
        
        ${profiles.length === 0 ? `
          <div class="empty" style="padding:30px;margin-bottom:24px;">
            <ha-icon icon="mdi:remote" style="font-size:48px;color:#666;"></ha-icon>
            <h4 style="margin:12px 0 8px;">No Custom Profiles Yet</h4>
            <p style="color:#888;">Create your first custom remote layout below!</p>
          </div>
        ` : `
          <div class="grid" style="margin-bottom:24px;">
            ${profiles.map(p => `
              <div class="card profile-card" data-profile-id="${p.id}">
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                  <div class="profile-icon" style="width:48px;height:48px;background:#2a2a4a;border-radius:8px;display:flex;align-items:center;justify-content:center;">
                    <ha-icon icon="${p.icon || 'mdi:remote'}" style="font-size:24px;color:#64b5f6;"></ha-icon>
                  </div>
                  <div style="flex:1;">
                    <div style="font-weight:600;">${p.name}</div>
                    <div style="color:#888;font-size:12px;">${p.device_type} • ${p.rows}×${p.cols} grid • ${(p.buttons || []).length} buttons</div>
                  </div>
                </div>
                ${p.description ? `<p style="color:#888;font-size:13px;margin:0 0 12px 0;">${p.description}</p>` : ''}
                <div class="card-actions">
                  <button class="btn btn-sm btn-p" data-action="builder-edit" data-profile-id="${p.id}">
                    <ha-icon icon="mdi:pencil"></ha-icon> Edit
                  </button>
                  <button class="btn btn-sm" data-action="builder-duplicate" data-profile-id="${p.id}">
                    <ha-icon icon="mdi:content-copy"></ha-icon> Duplicate
                  </button>
                  <button class="btn btn-sm btn-danger" data-action="builder-delete" data-profile-id="${p.id}">
                    <ha-icon icon="mdi:delete"></ha-icon>
                  </button>
                </div>
              </div>
            `).join('')}
          </div>
        `}

        <!-- Device Templates Section -->
        <div class="section-header" style="margin-top:32px;">
          <h3><ha-icon icon="mdi:devices"></ha-icon> Device Templates</h3>
        </div>
        <p style="color:#888;margin-bottom:16px;">Pre-configured remotes for common devices.</p>
        
        <div class="grid templates-grid">
          ${basicTemplates.map(t => `
            <div class="card template-card" data-template-id="${t.id}" data-action="builder-from-template" style="cursor:pointer;transition:all 0.2s;">
              <div style="text-align:center;padding:20px 0;">
                <ha-icon icon="${t.icon}" style="font-size:36px;color:#64b5f6;"></ha-icon>
                <h4 style="margin:12px 0 4px;font-size:15px;">${t.name}</h4>
                <div style="color:#888;font-size:12px;">${t.rows}×${t.cols} grid</div>
              </div>
            </div>
          `).join('')}
        </div>
        
        <!-- Design Variations Section -->
        <div class="section-header" style="margin-top:32px;">
          <h3><ha-icon icon="mdi:palette"></ha-icon> Design Variations</h3>
        </div>
        <p style="color:#888;margin-bottom:16px;">Alternative button styles and color schemes.</p>
        
        <div class="grid templates-grid">
          ${designTemplates.map(t => `
            <div class="card template-card" data-template-id="${t.id}" data-action="builder-from-template" style="cursor:pointer;transition:all 0.2s;position:relative;">
              <div style="text-align:center;padding:20px 0;">
                <ha-icon icon="${t.icon}" style="font-size:36px;color:${t.id.includes('backlit') ? '#00e5ff' : t.id.includes('blackout') ? '#333' : '#64b5f6'};"></ha-icon>
                <h4 style="margin:12px 0 4px;font-size:15px;">${t.name}</h4>
                <div style="color:#888;font-size:11px;">${t.desc || ''}</div>
              </div>
            </div>
          `).join('')}
        </div>

        <!-- Create Blank -->
        <div class="section-header" style="margin-top:32px;">
          <h3><ha-icon icon="mdi:plus-box"></ha-icon> Create Blank</h3>
        </div>
        <div class="card" style="padding:20px;">
          <p style="color:#888;margin:0 0 16px;">Start with an empty grid and add buttons manually.</p>
          <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
            <div class="fg" style="flex:1;min-width:150px;">
              <label class="fl">Name</label>
              <input type="text" class="fi" id="builder-new-name" placeholder="My Remote">
            </div>
            <div class="fg" style="width:80px;">
              <label class="fl">Rows</label>
              <input type="number" class="fi" id="builder-new-rows" value="8" min="2" max="20">
            </div>
            <div class="fg" style="width:80px;">
              <label class="fl">Cols</label>
              <input type="number" class="fi" id="builder-new-cols" value="4" min="2" max="6">
            </div>
            <button class="btn btn-p" data-action="builder-create-blank" style="margin-top:20px;">
              <ha-icon icon="mdi:plus"></ha-icon> Create
            </button>
          </div>
        </div>
      </div>
      
      <style>
        .templates-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
        .template-card:hover { background: #2a2a4a !important; transform: translateY(-2px); }
        .profile-card:hover { background: #1e1e38; }
      </style>
    `;
  }

  _profileEditorView() {
    const profile = this._builderProfile;
    if (!profile) return '<div class="empty">Profile not loaded</div>';

    const rows = profile.rows || 8;
    const cols = profile.cols || 4;
    const buttons = profile.buttons || [];
    const cellSize = 70;
    const gridWidth = cols * cellSize;
    const gridHeight = rows * cellSize;

    // Create grid cells
    const gridCells = [];
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        // Check if this cell is occupied by a button
        const btn = buttons.find(b => b.row === r && b.col === c);
        if (btn) {
          gridCells.push(this._renderBuilderButton(btn, cellSize));
        } else {
          // Check if this cell is covered by a spanning button
          const covered = buttons.find(b => 
            b.row <= r && b.row + (b.row_span || 1) > r &&
            b.col <= c && b.col + (b.col_span || 1) > c &&
            !(b.row === r && b.col === c)
          );
          if (!covered) {
            gridCells.push(`
              <div class="grid-cell empty-cell" data-row="${r}" data-col="${c}" data-action="builder-add-button"
                   style="grid-row:${r+1};grid-column:${c+1};width:${cellSize}px;height:${cellSize}px;
                          border:1px dashed #444;border-radius:4px;display:flex;align-items:center;justify-content:center;
                          cursor:pointer;transition:all 0.2s;">
                <ha-icon icon="mdi:plus" style="color:#555;font-size:20px;"></ha-icon>
              </div>
            `);
          }
        }
      }
    }

    const selectedBtn = this._builderSelectedButton ? 
      buttons.find(b => b.id === this._builderSelectedButton) : null;

    return `
      <div class="builder-editor" style="display:flex;gap:24px;flex-wrap:wrap;">
        <!-- Left: Grid Editor -->
        <div class="builder-grid-container" style="flex:1;min-width:300px;">
          <div class="card" style="padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
              <div>
                <input type="text" class="fi" id="builder-profile-name" value="${profile.name || 'My Remote'}" 
                       style="font-size:18px;font-weight:600;background:transparent;border:none;border-bottom:1px solid #444;padding:4px 0;width:200px;">
                <div style="color:#888;font-size:12px;margin-top:4px;">${rows}×${cols} grid • ${buttons.length} buttons</div>
              </div>
              <div style="display:flex;gap:8px;">
                <button class="btn btn-sm" data-action="builder-settings" title="Grid Settings">
                  <ha-icon icon="mdi:cog"></ha-icon>
                </button>
                <button class="btn btn-sm" data-action="builder-clear" title="Clear All">
                  <ha-icon icon="mdi:delete-sweep"></ha-icon>
                </button>
              </div>
            </div>
            
            <!-- Visual Grid -->
            <div class="builder-grid" style="display:grid;grid-template-columns:repeat(${cols}, ${cellSize}px);
                 grid-template-rows:repeat(${rows}, ${cellSize}px);gap:4px;background:#1a1a2e;padding:12px;border-radius:8px;
                 width:fit-content;margin:0 auto;">
              ${gridCells.join('')}
            </div>
            
            <div style="text-align:center;margin-top:12px;color:#666;font-size:12px;">
              Click empty cell to add button • Click button to edit • Drag to move
            </div>
          </div>
        </div>

        <!-- Right: Button Properties Panel -->
        <div class="builder-properties" style="width:320px;flex-shrink:0;">
          ${selectedBtn ? this._renderButtonProperties(selectedBtn) : `
            <div class="card" style="padding:24px;text-align:center;">
              <ha-icon icon="mdi:gesture-tap" style="font-size:48px;color:#444;"></ha-icon>
              <h4 style="margin:12px 0 8px;color:#888;">Select a Button</h4>
              <p style="color:#666;font-size:13px;">Click a button on the grid to edit its properties, or click an empty cell to add a new button.</p>
            </div>
          `}

          <!-- Quick Add Buttons -->
          <div class="card" style="margin-top:16px;padding:16px;">
            <h4 style="margin:0 0 12px;font-size:14px;">Quick Add</h4>
            <div style="display:flex;flex-wrap:wrap;gap:6px;">
              ${this._getQuickAddButtons().map(qb => `
                <button class="btn btn-sm" data-action="builder-quick-add" data-button-type="${qb.type}" 
                        data-icon="${qb.icon}" data-label="${qb.label}" title="${qb.label}">
                  <ha-icon icon="${qb.icon}"></ha-icon>
                </button>
              `).join('')}
            </div>
          </div>

          <!-- Device Assignment -->
          <div class="card" style="margin-top:16px;padding:16px;">
            <h4 style="margin:0 0 12px;font-size:14px;">Default Device</h4>
            <select class="fi" id="builder-default-device">
              <option value="">-- Select Device --</option>
              ${(this._data.devices || []).map(d => `
                <option value="${d.id}" ${profile.default_device_id === d.id ? 'selected' : ''}>${d.name}</option>
              `).join('')}
            </select>
            <p style="color:#666;font-size:11px;margin-top:8px;">Buttons without a specific device will use this one.</p>
          </div>
        </div>
      </div>

      <style>
        .builder-grid .empty-cell:hover { background: #2a2a4a !important; border-color: #64b5f6 !important; }
        .builder-grid .remote-button:hover { transform: scale(1.05); }
        .builder-grid .remote-button.selected { outline: 2px solid #64b5f6; outline-offset: 2px; }
        .builder-properties .fg { margin-bottom: 12px; }
      </style>
    `;
  }

  _renderBuilderButton(btn, cellSize) {
    const width = (btn.col_span || 1) * cellSize + ((btn.col_span || 1) - 1) * 4;
    const height = (btn.row_span || 1) * cellSize + ((btn.row_span || 1) - 1) * 4;
    const isSelected = this._builderSelectedButton === btn.id;
    const bgColor = btn.color || '#3d5afe';
    const shape = btn.shape || 'square';
    const borderRadius = shape === 'circle' ? '50%' : shape === 'oval' ? '40%' : '8px';

    return `
      <div class="remote-button ${isSelected ? 'selected' : ''}" 
           data-button-id="${btn.id}" data-action="builder-select-button"
           style="grid-row:${btn.row+1}/span ${btn.row_span || 1};grid-column:${btn.col+1}/span ${btn.col_span || 1};
                  width:${width}px;height:${height}px;background:${bgColor};border-radius:${borderRadius};
                  display:flex;flex-direction:column;align-items:center;justify-content:center;cursor:pointer;
                  transition:all 0.15s;box-shadow:0 2px 4px rgba(0,0,0,0.3);">
        ${btn.icon ? `<ha-icon icon="${btn.icon}" style="font-size:${Math.min(width, height) * 0.4}px;color:#fff;"></ha-icon>` : ''}
        ${btn.label && (!btn.icon || height > 60) ? `<span style="font-size:10px;color:#fff;margin-top:2px;text-align:center;padding:0 4px;">${btn.label}</span>` : ''}
      </div>
    `;
  }

  _renderButtonProperties(btn) {
    const devices = this._data.devices || [];
    const scenes = this._data.scenes || [];
    const actionTypes = [
      { value: 'ir_command', label: 'IR Command' },
      { value: 'ha_service', label: 'HA Service' },
      { value: 'scene', label: 'OmniRemote Scene' },
      { value: 'none', label: 'No Action' },
    ];

    const buttonTypes = [
      'power', 'volume', 'channel', 'navigation', 'playback', 'number', 'input', 'menu', 'color', 'custom'
    ];

    const shapes = [
      { value: 'square', label: 'Square' },
      { value: 'circle', label: 'Circle' },
      { value: 'rectangle', label: 'Rectangle' },
      { value: 'oval', label: 'Oval' },
    ];

    return `
      <div class="card" style="padding:16px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
          <h4 style="margin:0;font-size:14px;">Button Properties</h4>
          <button class="btn btn-sm btn-danger" data-action="builder-delete-button" data-button-id="${btn.id}">
            <ha-icon icon="mdi:delete"></ha-icon>
          </button>
        </div>

        <div class="fg">
          <label class="fl">Label</label>
          <input type="text" class="fi builder-prop" data-prop="label" value="${btn.label || ''}" placeholder="Button label">
        </div>

        <div class="fg">
          <label class="fl">Icon</label>
          <div style="display:flex;gap:8px;">
            <input type="text" class="fi builder-prop" data-prop="icon" value="${btn.icon || ''}" placeholder="mdi:power" style="flex:1;">
            <button class="btn btn-sm" data-action="builder-pick-icon" title="Pick Icon">
              <ha-icon icon="${btn.icon || 'mdi:emoticon-outline'}"></ha-icon>
            </button>
          </div>
        </div>

        <div style="display:flex;gap:8px;">
          <div class="fg" style="flex:1;">
            <label class="fl">Shape</label>
            <select class="fi builder-prop" data-prop="shape">
              ${shapes.map(s => `<option value="${s.value}" ${btn.shape === s.value ? 'selected' : ''}>${s.label}</option>`).join('')}
            </select>
          </div>
          <div class="fg" style="flex:1;">
            <label class="fl">Color</label>
            <input type="color" class="fi builder-prop" data-prop="color" value="${btn.color || '#3d5afe'}" style="height:36px;padding:2px;">
          </div>
        </div>

        <div style="display:flex;gap:8px;">
          <div class="fg" style="flex:1;">
            <label class="fl">Width (cells)</label>
            <input type="number" class="fi builder-prop" data-prop="col_span" value="${btn.col_span || 1}" min="1" max="4">
          </div>
          <div class="fg" style="flex:1;">
            <label class="fl">Height (cells)</label>
            <input type="number" class="fi builder-prop" data-prop="row_span" value="${btn.row_span || 1}" min="1" max="4">
          </div>
        </div>

        <hr style="border:none;border-top:1px solid #333;margin:16px 0;">

        <div class="fg">
          <label class="fl">Action Type</label>
          <select class="fi builder-prop" data-prop="action_type" id="builder-action-type">
            ${actionTypes.map(a => `<option value="${a.value}" ${btn.action_type === a.value ? 'selected' : ''}>${a.label}</option>`).join('')}
          </select>
        </div>

        <!-- IR Command Options -->
        <div id="action-ir-options" style="display:${btn.action_type === 'ir_command' || !btn.action_type ? 'block' : 'none'};">
          <div class="fg">
            <label class="fl">Device</label>
            <select class="fi builder-prop" data-prop="device_id">
              <option value="">-- Use Default --</option>
              ${devices.map(d => `<option value="${d.id}" ${btn.device_id === d.id ? 'selected' : ''}>${d.name}</option>`).join('')}
            </select>
          </div>
          <div class="fg">
            <label class="fl">Command</label>
            <input type="text" class="fi builder-prop" data-prop="command_name" value="${btn.command_name || ''}" placeholder="power, volume_up, etc.">
          </div>
        </div>

        <!-- Scene Options -->
        <div id="action-scene-options" style="display:${btn.action_type === 'scene' ? 'block' : 'none'};">
          <div class="fg">
            <label class="fl">Scene</label>
            <select class="fi builder-prop" data-prop="scene_id">
              <option value="">-- Select Scene --</option>
              ${scenes.map(s => `<option value="${s.id}" ${btn.scene_id === s.id ? 'selected' : ''}>${s.name}</option>`).join('')}
            </select>
          </div>
          <div class="fg">
            <label class="fl">Action</label>
            <select class="fi builder-prop" data-prop="scene_action">
              <option value="on" ${btn.scene_action === 'on' ? 'selected' : ''}>Turn On</option>
              <option value="off" ${btn.scene_action === 'off' ? 'selected' : ''}>Turn Off</option>
            </select>
          </div>
        </div>

        <!-- HA Service Options -->
        <div id="action-ha-options" style="display:${btn.action_type === 'ha_service' ? 'block' : 'none'};">
          <div class="fg">
            <label class="fl">Domain</label>
            <input type="text" class="fi builder-prop" data-prop="ha_domain" value="${btn.ha_domain || ''}" placeholder="light, switch, media_player...">
          </div>
          <div class="fg">
            <label class="fl">Service</label>
            <input type="text" class="fi builder-prop" data-prop="ha_service" value="${btn.ha_service || ''}" placeholder="turn_on, toggle...">
          </div>
          <div class="fg">
            <label class="fl">Entity ID</label>
            <input type="text" class="fi builder-prop" data-prop="ha_entity_id" value="${btn.ha_entity_id || ''}" placeholder="light.living_room">
          </div>
        </div>

        <div style="margin-top:16px;text-align:right;">
          <button class="btn btn-p" data-action="builder-apply-props">
            <ha-icon icon="mdi:check"></ha-icon> Apply
          </button>
        </div>
      </div>
    `;
  }

  _getQuickAddButtons() {
    return [
      { type: 'power', icon: 'mdi:power', label: 'Power' },
      { type: 'vol_up', icon: 'mdi:volume-plus', label: 'Vol +' },
      { type: 'vol_down', icon: 'mdi:volume-minus', label: 'Vol -' },
      { type: 'mute', icon: 'mdi:volume-off', label: 'Mute' },
      { type: 'ch_up', icon: 'mdi:chevron-up', label: 'CH +' },
      { type: 'ch_down', icon: 'mdi:chevron-down', label: 'CH -' },
      { type: 'up', icon: 'mdi:arrow-up', label: 'Up' },
      { type: 'down', icon: 'mdi:arrow-down', label: 'Down' },
      { type: 'left', icon: 'mdi:arrow-left', label: 'Left' },
      { type: 'right', icon: 'mdi:arrow-right', label: 'Right' },
      { type: 'ok', icon: 'mdi:check-circle', label: 'OK' },
      { type: 'back', icon: 'mdi:arrow-u-left-top', label: 'Back' },
      { type: 'home', icon: 'mdi:home', label: 'Home' },
      { type: 'menu', icon: 'mdi:menu', label: 'Menu' },
      { type: 'play', icon: 'mdi:play', label: 'Play' },
      { type: 'pause', icon: 'mdi:pause', label: 'Pause' },
      { type: 'stop', icon: 'mdi:stop', label: 'Stop' },
      { type: 'input', icon: 'mdi:import', label: 'Input' },
    ];
  }

  // Builder action handlers
  async _handleBuilderAction(action, data) {
    switch (action) {
      case 'builder-new':
        this._showBuilderNewModal();
        break;

      case 'builder-create-blank':
        const name = this.shadowRoot.getElementById('builder-new-name')?.value || 'My Remote';
        const rows = parseInt(this.shadowRoot.getElementById('builder-new-rows')?.value) || 8;
        const cols = parseInt(this.shadowRoot.getElementById('builder-new-cols')?.value) || 4;
        this._createNewProfile(name, rows, cols);
        break;

      case 'builder-from-template':
        await this._createFromTemplate(data.templateId);
        break;

      case 'builder-edit':
        await this._loadProfileForEditing(data.profileId);
        break;

      case 'builder-duplicate':
        await this._duplicateProfile(data.profileId);
        break;

      case 'builder-delete':
        if (confirm('Delete this remote profile?')) {
          await this._deleteProfile(data.profileId);
        }
        break;

      case 'builder-back':
        this._builderProfileId = null;
        this._builderProfile = null;
        this._builderSelectedButton = null;
        this._render();
        break;

      case 'builder-save':
        await this._saveBuilderProfile();
        break;

      case 'builder-preview':
        this._builderPreviewMode = !this._builderPreviewMode;
        this._render();
        break;

      case 'builder-add-button':
        this._addButtonAtCell(parseInt(data.row), parseInt(data.col));
        break;

      case 'builder-select-button':
        this._builderSelectedButton = data.buttonId;
        this._render();
        this._setupBuilderPropertyHandlers();
        break;

      case 'builder-delete-button':
        this._deleteBuilderButton(data.buttonId);
        break;

      case 'builder-quick-add':
        this._quickAddButton(data.buttonType, data.icon, data.label);
        break;

      case 'builder-apply-props':
        this._applyButtonProperties();
        break;

      case 'builder-settings':
        this._showGridSettingsModal();
        break;

      case 'builder-clear':
        if (confirm('Clear all buttons from this remote?')) {
          this._builderProfile.buttons = [];
          this._builderSelectedButton = null;
          this._render();
        }
        break;

      case 'builder-pick-icon':
        this._showIconPickerForBuilder();
        break;
    }
  }

  _createNewProfile(name, rows, cols, template = null) {
    const id = 'profile_' + Date.now().toString(36);
    this._builderProfile = {
      id,
      name,
      description: '',
      icon: 'mdi:remote',
      rows,
      cols,
      device_type: 'universal',
      default_device_id: null,
      buttons: [],
      template,
    };
    this._builderProfileId = id;
    this._builderSelectedButton = null;
    this._render();
  }

  async _createFromTemplate(templateId) {
    const templates = {
      // === BASIC TEMPLATES ===
      tv_basic: {
        name: 'TV Remote', rows: 10, cols: 4, device_type: 'tv', icon: 'mdi:television',
        buttons: [
          { id: 'power', label: 'Power', icon: 'mdi:power', row: 0, col: 1, col_span: 2, color: '#f44336', command_name: 'power' },
          { id: 'input', label: 'Input', icon: 'mdi:import', row: 1, col: 0, command_name: 'source' },
          { id: 'mute', label: 'Mute', icon: 'mdi:volume-off', row: 1, col: 3, command_name: 'mute' },
          { id: 'vol_up', label: 'Vol +', icon: 'mdi:volume-plus', row: 2, col: 0, command_name: 'volume_up' },
          { id: 'ch_up', label: 'CH +', icon: 'mdi:chevron-up', row: 2, col: 3, command_name: 'channel_up' },
          { id: 'vol_down', label: 'Vol -', icon: 'mdi:volume-minus', row: 3, col: 0, command_name: 'volume_down' },
          { id: 'ch_down', label: 'CH -', icon: 'mdi:chevron-down', row: 3, col: 3, command_name: 'channel_down' },
          { id: 'up', label: '', icon: 'mdi:chevron-up', row: 5, col: 1, col_span: 2, command_name: 'up', shape: 'rectangle' },
          { id: 'left', label: '', icon: 'mdi:chevron-left', row: 6, col: 0, command_name: 'left' },
          { id: 'ok', label: 'OK', icon: 'mdi:check-circle', row: 6, col: 1, col_span: 2, color: '#4caf50', command_name: 'ok' },
          { id: 'right', label: '', icon: 'mdi:chevron-right', row: 6, col: 3, command_name: 'right' },
          { id: 'down', label: '', icon: 'mdi:chevron-down', row: 7, col: 1, col_span: 2, command_name: 'down', shape: 'rectangle' },
          { id: 'back', label: 'Back', icon: 'mdi:arrow-left', row: 8, col: 0, command_name: 'back' },
          { id: 'home', label: 'Home', icon: 'mdi:home', row: 8, col: 1, col_span: 2, command_name: 'home' },
          { id: 'menu', label: 'Menu', icon: 'mdi:menu', row: 8, col: 3, command_name: 'menu' },
        ]
      },
      receiver: {
        name: 'AV Receiver', rows: 12, cols: 4, device_type: 'receiver', icon: 'mdi:speaker',
        buttons: [
          { id: 'power', label: 'Power', icon: 'mdi:power', row: 0, col: 1, col_span: 2, color: '#f44336', command_name: 'power' },
          { id: 'vol_up', label: 'Vol +', icon: 'mdi:volume-plus', row: 1, col: 0, command_name: 'volume_up' },
          { id: 'mute', label: 'Mute', icon: 'mdi:volume-off', row: 1, col: 1, col_span: 2, command_name: 'mute' },
          { id: 'vol_down', label: 'Vol -', icon: 'mdi:volume-minus', row: 1, col: 3, command_name: 'volume_down' },
          { id: 'hdmi1', label: 'HDMI 1', icon: 'mdi:hdmi-port', row: 3, col: 0, command_name: 'hdmi1' },
          { id: 'hdmi2', label: 'HDMI 2', icon: 'mdi:hdmi-port', row: 3, col: 1, command_name: 'hdmi2' },
          { id: 'hdmi3', label: 'HDMI 3', icon: 'mdi:hdmi-port', row: 3, col: 2, command_name: 'hdmi3' },
          { id: 'hdmi4', label: 'HDMI 4', icon: 'mdi:hdmi-port', row: 3, col: 3, command_name: 'hdmi4' },
          { id: 'optical', label: 'Optical', icon: 'mdi:toslink', row: 4, col: 0, command_name: 'optical' },
          { id: 'bluetooth', label: 'BT', icon: 'mdi:bluetooth', row: 4, col: 1, command_name: 'bluetooth' },
          { id: 'aux', label: 'AUX', icon: 'mdi:audio-input-rca', row: 4, col: 2, command_name: 'aux' },
          { id: 'tv', label: 'TV', icon: 'mdi:television', row: 4, col: 3, command_name: 'tv' },
          { id: 'stereo', label: 'Stereo', icon: 'mdi:speaker-stereo', row: 6, col: 0, command_name: 'stereo' },
          { id: 'surround', label: 'Surround', icon: 'mdi:surround-sound', row: 6, col: 1, command_name: 'surround' },
          { id: 'movie', label: 'Movie', icon: 'mdi:movie', row: 6, col: 2, command_name: 'movie' },
          { id: 'music', label: 'Music', icon: 'mdi:music', row: 6, col: 3, command_name: 'music' },
        ]
      },
      streaming: {
        name: 'Streaming Remote', rows: 8, cols: 3, device_type: 'streaming', icon: 'mdi:cast',
        buttons: [
          { id: 'power', label: 'Power', icon: 'mdi:power', row: 0, col: 1, color: '#f44336', command_name: 'power' },
          { id: 'up', label: '', icon: 'mdi:chevron-up', row: 1, col: 1, command_name: 'up' },
          { id: 'left', label: '', icon: 'mdi:chevron-left', row: 2, col: 0, command_name: 'left' },
          { id: 'ok', label: 'OK', icon: 'mdi:check-circle', row: 2, col: 1, color: '#4caf50', command_name: 'ok' },
          { id: 'right', label: '', icon: 'mdi:chevron-right', row: 2, col: 2, command_name: 'right' },
          { id: 'down', label: '', icon: 'mdi:chevron-down', row: 3, col: 1, command_name: 'down' },
          { id: 'back', label: 'Back', icon: 'mdi:arrow-left', row: 4, col: 0, command_name: 'back' },
          { id: 'home', label: 'Home', icon: 'mdi:home', row: 4, col: 1, command_name: 'home' },
          { id: 'menu', label: 'Menu', icon: 'mdi:menu', row: 4, col: 2, command_name: 'menu' },
          { id: 'play', label: '', icon: 'mdi:play-pause', row: 5, col: 1, command_name: 'play_pause' },
          { id: 'rw', label: '', icon: 'mdi:rewind', row: 5, col: 0, command_name: 'rewind' },
          { id: 'ff', label: '', icon: 'mdi:fast-forward', row: 5, col: 2, command_name: 'fast_forward' },
          { id: 'vol_up', label: 'Vol +', icon: 'mdi:volume-plus', row: 6, col: 0, command_name: 'volume_up' },
          { id: 'mute', label: 'Mute', icon: 'mdi:volume-off', row: 6, col: 1, command_name: 'mute' },
          { id: 'vol_down', label: 'Vol -', icon: 'mdi:volume-minus', row: 6, col: 2, command_name: 'volume_down' },
        ]
      },
      soundbar: {
        name: 'Soundbar', rows: 6, cols: 3, device_type: 'soundbar', icon: 'mdi:speaker-wireless',
        buttons: [
          { id: 'power', label: 'Power', icon: 'mdi:power', row: 0, col: 1, color: '#f44336', command_name: 'power' },
          { id: 'vol_up', label: 'Vol +', icon: 'mdi:volume-plus', row: 1, col: 1, row_span: 2, command_name: 'volume_up', color: '#4caf50' },
          { id: 'mute', label: 'Mute', icon: 'mdi:volume-off', row: 3, col: 1, command_name: 'mute' },
          { id: 'vol_down', label: 'Vol -', icon: 'mdi:volume-minus', row: 4, col: 1, row_span: 2, command_name: 'volume_down', color: '#2196f3' },
          { id: 'input', label: 'Input', icon: 'mdi:import', row: 1, col: 0, command_name: 'source' },
          { id: 'bluetooth', label: 'BT', icon: 'mdi:bluetooth', row: 2, col: 0, command_name: 'bluetooth' },
          { id: 'optical', label: 'Opt', icon: 'mdi:toslink', row: 1, col: 2, command_name: 'optical' },
          { id: 'hdmi', label: 'HDMI', icon: 'mdi:hdmi-port', row: 2, col: 2, command_name: 'hdmi_arc' },
          { id: 'bass_up', label: 'Bass +', icon: 'mdi:plus', row: 4, col: 0, command_name: 'bass_up' },
          { id: 'bass_down', label: 'Bass -', icon: 'mdi:minus', row: 4, col: 2, command_name: 'bass_down' },
        ]
      },
      projector: {
        name: 'Projector', rows: 10, cols: 4, device_type: 'projector', icon: 'mdi:projector',
        buttons: [
          { id: 'power', label: 'Power', icon: 'mdi:power', row: 0, col: 0, col_span: 2, color: '#f44336', command_name: 'power' },
          { id: 'power_off', label: 'Off', icon: 'mdi:power-off', row: 0, col: 2, col_span: 2, color: '#616161', command_name: 'power_off' },
          { id: 'input', label: 'Input', icon: 'mdi:import', row: 1, col: 0, command_name: 'source' },
          { id: 'hdmi1', label: 'HDMI 1', icon: 'mdi:hdmi-port', row: 1, col: 1, command_name: 'hdmi1' },
          { id: 'hdmi2', label: 'HDMI 2', icon: 'mdi:hdmi-port', row: 1, col: 2, command_name: 'hdmi2' },
          { id: 'vga', label: 'VGA', icon: 'mdi:video-input-component', row: 1, col: 3, command_name: 'vga' },
          { id: 'blank', label: 'Blank', icon: 'mdi:rectangle', row: 2, col: 0, color: '#000000', command_name: 'blank' },
          { id: 'freeze', label: 'Freeze', icon: 'mdi:snowflake', row: 2, col: 1, color: '#2196f3', command_name: 'freeze' },
          { id: 'aspect', label: 'Aspect', icon: 'mdi:aspect-ratio', row: 2, col: 2, command_name: 'aspect' },
          { id: 'keystone', label: 'Keystone', icon: 'mdi:shape-polygon-plus', row: 2, col: 3, command_name: 'keystone' },
          { id: 'up', label: '', icon: 'mdi:chevron-up', row: 4, col: 1, col_span: 2, command_name: 'up' },
          { id: 'left', label: '', icon: 'mdi:chevron-left', row: 5, col: 0, command_name: 'left' },
          { id: 'ok', label: 'OK', icon: 'mdi:check-circle', row: 5, col: 1, col_span: 2, color: '#4caf50', command_name: 'ok' },
          { id: 'right', label: '', icon: 'mdi:chevron-right', row: 5, col: 3, command_name: 'right' },
          { id: 'down', label: '', icon: 'mdi:chevron-down', row: 6, col: 1, col_span: 2, command_name: 'down' },
          { id: 'menu', label: 'Menu', icon: 'mdi:menu', row: 7, col: 0, command_name: 'menu' },
          { id: 'back', label: 'Back', icon: 'mdi:arrow-left', row: 7, col: 1, command_name: 'back' },
          { id: 'auto', label: 'Auto', icon: 'mdi:auto-fix', row: 7, col: 2, command_name: 'auto' },
          { id: 'eco', label: 'Eco', icon: 'mdi:leaf', row: 7, col: 3, color: '#4caf50', command_name: 'eco' },
          { id: 'zoom_in', label: 'Zoom +', icon: 'mdi:magnify-plus', row: 8, col: 0, command_name: 'zoom_in' },
          { id: 'zoom_out', label: 'Zoom -', icon: 'mdi:magnify-minus', row: 8, col: 1, command_name: 'zoom_out' },
          { id: 'focus_near', label: 'Focus -', icon: 'mdi:camera-metering-center', row: 8, col: 2, command_name: 'focus_near' },
          { id: 'focus_far', label: 'Focus +', icon: 'mdi:camera-metering-spot', row: 8, col: 3, command_name: 'focus_far' },
        ]
      },
      ac: {
        name: 'Air Conditioner', rows: 8, cols: 4, device_type: 'ac', icon: 'mdi:air-conditioner',
        buttons: [
          { id: 'power', label: 'Power', icon: 'mdi:power', row: 0, col: 1, col_span: 2, color: '#f44336', command_name: 'power' },
          { id: 'temp_up', label: '', icon: 'mdi:thermometer-chevron-up', row: 1, col: 0, col_span: 2, row_span: 2, color: '#ff5722', command_name: 'temp_up' },
          { id: 'temp_down', label: '', icon: 'mdi:thermometer-chevron-down', row: 1, col: 2, col_span: 2, row_span: 2, color: '#2196f3', command_name: 'temp_down' },
          { id: 'cool', label: 'Cool', icon: 'mdi:snowflake', row: 4, col: 0, color: '#2196f3', command_name: 'cool' },
          { id: 'heat', label: 'Heat', icon: 'mdi:fire', row: 4, col: 1, color: '#ff5722', command_name: 'heat' },
          { id: 'auto', label: 'Auto', icon: 'mdi:autorenew', row: 4, col: 2, color: '#4caf50', command_name: 'auto' },
          { id: 'dry', label: 'Dry', icon: 'mdi:water-percent', row: 4, col: 3, color: '#ff9800', command_name: 'dry' },
          { id: 'fan_low', label: 'Low', icon: 'mdi:fan-speed-1', row: 5, col: 0, command_name: 'fan_low' },
          { id: 'fan_med', label: 'Med', icon: 'mdi:fan-speed-2', row: 5, col: 1, command_name: 'fan_med' },
          { id: 'fan_high', label: 'High', icon: 'mdi:fan-speed-3', row: 5, col: 2, command_name: 'fan_high' },
          { id: 'fan_auto', label: 'Auto', icon: 'mdi:fan-auto', row: 5, col: 3, command_name: 'fan_auto' },
          { id: 'swing', label: 'Swing', icon: 'mdi:arrow-oscillating', row: 6, col: 0, command_name: 'swing' },
          { id: 'timer', label: 'Timer', icon: 'mdi:timer', row: 6, col: 1, command_name: 'timer' },
          { id: 'sleep', label: 'Sleep', icon: 'mdi:bed', row: 6, col: 2, command_name: 'sleep' },
          { id: 'turbo', label: 'Turbo', icon: 'mdi:lightning-bolt', row: 6, col: 3, color: '#ff9800', command_name: 'turbo' },
        ]
      },
      fan: {
        name: 'Ceiling Fan', rows: 6, cols: 3, device_type: 'fan', icon: 'mdi:ceiling-fan',
        buttons: [
          { id: 'power', label: 'Power', icon: 'mdi:power', row: 0, col: 1, color: '#f44336', command_name: 'power' },
          { id: 'light', label: 'Light', icon: 'mdi:lightbulb', row: 0, col: 2, color: '#ffeb3b', command_name: 'light' },
          { id: 'speed_1', label: 'Low', icon: 'mdi:fan-speed-1', row: 2, col: 0, command_name: 'speed_1' },
          { id: 'speed_2', label: 'Med', icon: 'mdi:fan-speed-2', row: 2, col: 1, command_name: 'speed_2' },
          { id: 'speed_3', label: 'High', icon: 'mdi:fan-speed-3', row: 2, col: 2, command_name: 'speed_3' },
          { id: 'reverse', label: 'Reverse', icon: 'mdi:rotate-3d-variant', row: 4, col: 0, command_name: 'reverse' },
          { id: 'timer', label: 'Timer', icon: 'mdi:timer', row: 4, col: 1, command_name: 'timer' },
          { id: 'breeze', label: 'Breeze', icon: 'mdi:weather-windy', row: 4, col: 2, command_name: 'breeze' },
        ]
      },
      // === DESIGN VARIATIONS ===
      tv_blackout: {
        name: 'TV Blackout', rows: 10, cols: 4, device_type: 'tv', icon: 'mdi:television',
        description: 'Dark theme with subtle button outlines',
        buttons: [
          { id: 'power', label: '', icon: 'mdi:power', row: 0, col: 1, col_span: 2, color: '#1a1a1a', command_name: 'power', shape: 'circle' },
          { id: 'input', label: '', icon: 'mdi:import', row: 1, col: 0, color: '#1a1a1a', command_name: 'source' },
          { id: 'mute', label: '', icon: 'mdi:volume-off', row: 1, col: 3, color: '#1a1a1a', command_name: 'mute' },
          { id: 'vol_up', label: '', icon: 'mdi:volume-plus', row: 2, col: 0, color: '#1a1a1a', command_name: 'volume_up' },
          { id: 'ch_up', label: '', icon: 'mdi:chevron-up', row: 2, col: 3, color: '#1a1a1a', command_name: 'channel_up' },
          { id: 'vol_down', label: '', icon: 'mdi:volume-minus', row: 3, col: 0, color: '#1a1a1a', command_name: 'volume_down' },
          { id: 'ch_down', label: '', icon: 'mdi:chevron-down', row: 3, col: 3, color: '#1a1a1a', command_name: 'channel_down' },
          { id: 'up', label: '', icon: 'mdi:chevron-up', row: 5, col: 1, col_span: 2, color: '#1a1a1a', command_name: 'up' },
          { id: 'left', label: '', icon: 'mdi:chevron-left', row: 6, col: 0, color: '#1a1a1a', command_name: 'left' },
          { id: 'ok', label: '', icon: 'mdi:circle-outline', row: 6, col: 1, col_span: 2, color: '#1a1a1a', command_name: 'ok', shape: 'circle' },
          { id: 'right', label: '', icon: 'mdi:chevron-right', row: 6, col: 3, color: '#1a1a1a', command_name: 'right' },
          { id: 'down', label: '', icon: 'mdi:chevron-down', row: 7, col: 1, col_span: 2, color: '#1a1a1a', command_name: 'down' },
          { id: 'back', label: '', icon: 'mdi:arrow-left', row: 8, col: 0, color: '#1a1a1a', command_name: 'back' },
          { id: 'home', label: '', icon: 'mdi:home', row: 8, col: 1, col_span: 2, color: '#1a1a1a', command_name: 'home' },
          { id: 'menu', label: '', icon: 'mdi:menu', row: 8, col: 3, color: '#1a1a1a', command_name: 'menu' },
        ]
      },
      tv_backlit: {
        name: 'TV Backlit', rows: 10, cols: 4, device_type: 'tv', icon: 'mdi:television',
        description: 'Glowing buttons with neon accents',
        buttons: [
          { id: 'power', label: 'Power', icon: 'mdi:power', row: 0, col: 1, col_span: 2, color: '#ff1744', command_name: 'power', shape: 'circle' },
          { id: 'input', label: 'Input', icon: 'mdi:import', row: 1, col: 0, color: '#00e5ff', command_name: 'source' },
          { id: 'mute', label: 'Mute', icon: 'mdi:volume-off', row: 1, col: 3, color: '#ff9100', command_name: 'mute' },
          { id: 'vol_up', label: '+', icon: 'mdi:volume-plus', row: 2, col: 0, color: '#00e676', command_name: 'volume_up' },
          { id: 'ch_up', label: '∧', icon: 'mdi:chevron-up', row: 2, col: 3, color: '#651fff', command_name: 'channel_up' },
          { id: 'vol_down', label: '-', icon: 'mdi:volume-minus', row: 3, col: 0, color: '#00e676', command_name: 'volume_down' },
          { id: 'ch_down', label: '∨', icon: 'mdi:chevron-down', row: 3, col: 3, color: '#651fff', command_name: 'channel_down' },
          { id: 'up', label: '', icon: 'mdi:triangle', row: 5, col: 1, col_span: 2, color: '#2979ff', command_name: 'up' },
          { id: 'left', label: '', icon: 'mdi:menu-left', row: 6, col: 0, color: '#2979ff', command_name: 'left' },
          { id: 'ok', label: 'OK', icon: 'mdi:radiobox-marked', row: 6, col: 1, col_span: 2, color: '#00e5ff', command_name: 'ok', shape: 'circle' },
          { id: 'right', label: '', icon: 'mdi:menu-right', row: 6, col: 3, color: '#2979ff', command_name: 'right' },
          { id: 'down', label: '', icon: 'mdi:triangle-down', row: 7, col: 1, col_span: 2, color: '#2979ff', command_name: 'down' },
          { id: 'back', label: 'Back', icon: 'mdi:keyboard-return', row: 8, col: 0, color: '#ff6e40', command_name: 'back' },
          { id: 'home', label: 'Home', icon: 'mdi:home-circle', row: 8, col: 1, col_span: 2, color: '#64ffda', command_name: 'home' },
          { id: 'menu', label: 'Menu', icon: 'mdi:dots-grid', row: 8, col: 3, color: '#ea80fc', command_name: 'menu' },
        ]
      },
      minimal_circle: {
        name: 'Minimal Circles', rows: 8, cols: 3, device_type: 'universal', icon: 'mdi:circle-outline',
        description: 'Clean circular button design',
        buttons: [
          { id: 'power', label: '', icon: 'mdi:power', row: 0, col: 1, color: '#f44336', command_name: 'power', shape: 'circle' },
          { id: 'up', label: '', icon: 'mdi:chevron-up', row: 2, col: 1, color: '#424242', command_name: 'up', shape: 'circle' },
          { id: 'left', label: '', icon: 'mdi:chevron-left', row: 3, col: 0, color: '#424242', command_name: 'left', shape: 'circle' },
          { id: 'ok', label: '', icon: 'mdi:checkbox-blank-circle', row: 3, col: 1, color: '#2196f3', command_name: 'ok', shape: 'circle' },
          { id: 'right', label: '', icon: 'mdi:chevron-right', row: 3, col: 2, color: '#424242', command_name: 'right', shape: 'circle' },
          { id: 'down', label: '', icon: 'mdi:chevron-down', row: 4, col: 1, color: '#424242', command_name: 'down', shape: 'circle' },
          { id: 'back', label: '', icon: 'mdi:arrow-left', row: 6, col: 0, color: '#616161', command_name: 'back', shape: 'circle' },
          { id: 'home', label: '', icon: 'mdi:home', row: 6, col: 1, color: '#616161', command_name: 'home', shape: 'circle' },
          { id: 'menu', label: '', icon: 'mdi:menu', row: 6, col: 2, color: '#616161', command_name: 'menu', shape: 'circle' },
        ]
      },
      gaming: {
        name: 'Gaming Controller', rows: 8, cols: 4, device_type: 'gaming', icon: 'mdi:gamepad-variant',
        description: 'Game controller style layout',
        buttons: [
          { id: 'power', label: '', icon: 'mdi:power', row: 0, col: 1, col_span: 2, color: '#4caf50', command_name: 'power', shape: 'circle' },
          { id: 'up', label: '', icon: 'mdi:chevron-up', row: 2, col: 0, color: '#424242', command_name: 'up' },
          { id: 'y', label: 'Y', row: 2, col: 2, color: '#ffc107', command_name: 'y', shape: 'circle' },
          { id: 'left', label: '', icon: 'mdi:chevron-left', row: 3, col: 0, color: '#424242', command_name: 'left' },
          { id: 'x', label: 'X', row: 3, col: 2, color: '#2196f3', command_name: 'x', shape: 'circle' },
          { id: 'b', label: 'B', row: 3, col: 3, color: '#f44336', command_name: 'b', shape: 'circle' },
          { id: 'down', label: '', icon: 'mdi:chevron-down', row: 4, col: 0, color: '#424242', command_name: 'down' },
          { id: 'a', label: 'A', row: 4, col: 3, color: '#4caf50', command_name: 'a', shape: 'circle' },
          { id: 'right', label: '', icon: 'mdi:chevron-right', row: 3, col: 1, color: '#424242', command_name: 'right' },
          { id: 'start', label: 'Start', icon: 'mdi:play', row: 6, col: 2, color: '#616161', command_name: 'start' },
          { id: 'select', label: 'Select', icon: 'mdi:checkbox-blank', row: 6, col: 1, color: '#616161', command_name: 'select' },
          { id: 'home', label: '', icon: 'mdi:home', row: 6, col: 3, color: '#ffffff', command_name: 'home', shape: 'circle' },
        ]
      },
      universal: {
        name: 'Blank Remote', rows: 8, cols: 4, device_type: 'universal', icon: 'mdi:remote',
        buttons: []
      },
    };

    const template = templates[templateId];
    if (!template) {
      alert('Template not found');
      return;
    }

    const id = 'profile_' + Date.now().toString(36);
    this._builderProfile = {
      id,
      name: template.name,
      description: '',
      icon: template.icon,
      rows: template.rows,
      cols: template.cols,
      device_type: template.device_type,
      default_device_id: null,
      buttons: template.buttons.map(b => ({
        ...b,
        id: b.id + '_' + Date.now().toString(36).slice(-4),
        action_type: 'ir_command',
      })),
      template: templateId,
    };
    this._builderProfileId = id;
    this._builderSelectedButton = null;
    this._render();
  }

  async _loadProfileForEditing(profileId) {
    const profile = (this._data.remoteProfiles || []).find(p => p.id === profileId);
    if (profile) {
      this._builderProfile = JSON.parse(JSON.stringify(profile)); // Deep clone
      this._builderProfileId = profileId;
      this._builderSelectedButton = null;
      this._render();
    }
  }

  async _duplicateProfile(profileId) {
    const profile = (this._data.remoteProfiles || []).find(p => p.id === profileId);
    if (profile) {
      const newProfile = JSON.parse(JSON.stringify(profile));
      newProfile.id = 'profile_' + Date.now().toString(36);
      newProfile.name = profile.name + ' (Copy)';
      
      const res = await this._api('/api/omniremote/remote_profiles', 'POST', {
        action: 'create',
        profile: newProfile,
      });
      
      if (res.success) {
        await this._loadData();
      } else {
        alert('Failed to duplicate: ' + (res.error || 'Unknown error'));
      }
    }
  }

  async _deleteProfile(profileId) {
    const res = await this._api('/api/omniremote/remote_profiles', 'POST', {
      action: 'delete',
      profile_id: profileId,
    });
    
    if (res.success) {
      await this._loadData();
    } else {
      alert('Failed to delete: ' + (res.error || 'Unknown error'));
    }
  }

  async _saveBuilderProfile() {
    if (!this._builderProfile) return;

    // Update name from input
    const nameInput = this.shadowRoot.getElementById('builder-profile-name');
    if (nameInput) {
      this._builderProfile.name = nameInput.value;
    }

    // Update default device
    const deviceSelect = this.shadowRoot.getElementById('builder-default-device');
    if (deviceSelect) {
      this._builderProfile.default_device_id = deviceSelect.value || null;
    }

    const res = await this._api('/api/omniremote/remote_profiles', 'POST', {
      action: 'save',
      profile: this._builderProfile,
    });

    if (res.success) {
      alert('Profile saved!');
      await this._loadData();
    } else {
      alert('Failed to save: ' + (res.error || 'Unknown error'));
    }
  }

  _addButtonAtCell(row, col) {
    if (!this._builderProfile) return;

    const id = 'btn_' + Date.now().toString(36);
    const newButton = {
      id,
      label: '',
      icon: 'mdi:circle',
      row,
      col,
      row_span: 1,
      col_span: 1,
      button_type: 'custom',
      shape: 'square',
      color: '#3d5afe',
      action_type: 'ir_command',
      device_id: null,
      command_name: null,
    };

    this._builderProfile.buttons.push(newButton);
    this._builderSelectedButton = id;
    this._render();
    this._setupBuilderPropertyHandlers();
  }

  _deleteBuilderButton(buttonId) {
    if (!this._builderProfile) return;
    this._builderProfile.buttons = this._builderProfile.buttons.filter(b => b.id !== buttonId);
    this._builderSelectedButton = null;
    this._render();
  }

  _quickAddButton(type, icon, label) {
    if (!this._builderProfile) return;

    // Find first empty cell
    const buttons = this._builderProfile.buttons;
    const rows = this._builderProfile.rows;
    const cols = this._builderProfile.cols;

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const occupied = buttons.some(b => 
          b.row <= r && b.row + (b.row_span || 1) > r &&
          b.col <= c && b.col + (b.col_span || 1) > c
        );
        if (!occupied) {
          const id = 'btn_' + Date.now().toString(36);
          buttons.push({
            id,
            label,
            icon,
            row: r,
            col: c,
            row_span: 1,
            col_span: 1,
            button_type: type,
            shape: 'square',
            color: type === 'power' ? '#f44336' : type === 'ok' ? '#4caf50' : '#3d5afe',
            action_type: 'ir_command',
            command_name: type,
          });
          this._builderSelectedButton = id;
          this._render();
          this._setupBuilderPropertyHandlers();
          return;
        }
      }
    }
    alert('No empty cells available');
  }

  _setupBuilderPropertyHandlers() {
    setTimeout(() => {
      const props = this.shadowRoot.querySelectorAll('.builder-prop');
      props.forEach(input => {
        input.addEventListener('change', () => this._onBuilderPropChange(input));
        input.addEventListener('input', () => {
          if (input.type === 'color') this._onBuilderPropChange(input);
        });
      });

      // Action type visibility toggle
      const actionType = this.shadowRoot.getElementById('builder-action-type');
      if (actionType) {
        actionType.addEventListener('change', () => {
          const val = actionType.value;
          const irOpts = this.shadowRoot.getElementById('action-ir-options');
          const sceneOpts = this.shadowRoot.getElementById('action-scene-options');
          const haOpts = this.shadowRoot.getElementById('action-ha-options');
          if (irOpts) irOpts.style.display = val === 'ir_command' ? 'block' : 'none';
          if (sceneOpts) sceneOpts.style.display = val === 'scene' ? 'block' : 'none';
          if (haOpts) haOpts.style.display = val === 'ha_service' ? 'block' : 'none';
        });
      }
    }, 100);
  }

  _onBuilderPropChange(input) {
    if (!this._builderProfile || !this._builderSelectedButton) return;

    const btn = this._builderProfile.buttons.find(b => b.id === this._builderSelectedButton);
    if (!btn) return;

    const prop = input.dataset.prop;
    let value = input.value;

    // Handle numeric properties
    if (['row', 'col', 'row_span', 'col_span'].includes(prop)) {
      value = parseInt(value) || 1;
    }

    btn[prop] = value;
  }

  _applyButtonProperties() {
    // Properties are already applied via change handlers
    // Just re-render to show changes
    this._render();
    this._setupBuilderPropertyHandlers();
  }

  _showGridSettingsModal() {
    if (!this._builderProfile) return;

    this._modal = `
      <div class="modal-head">
        <h3>Grid Settings</h3>
        <button class="modal-close" data-action="close-modal">&times;</button>
      </div>
      <div class="fg">
        <label class="fl">Rows</label>
        <input type="number" class="fi" id="grid-rows" value="${this._builderProfile.rows}" min="2" max="20">
      </div>
      <div class="fg">
        <label class="fl">Columns</label>
        <input type="number" class="fi" id="grid-cols" value="${this._builderProfile.cols}" min="2" max="6">
      </div>
      <div class="fg">
        <label class="fl">Device Type</label>
        <select class="fi" id="grid-device-type">
          <option value="universal" ${this._builderProfile.device_type === 'universal' ? 'selected' : ''}>Universal</option>
          <option value="tv" ${this._builderProfile.device_type === 'tv' ? 'selected' : ''}>TV</option>
          <option value="receiver" ${this._builderProfile.device_type === 'receiver' ? 'selected' : ''}>Receiver</option>
          <option value="streaming" ${this._builderProfile.device_type === 'streaming' ? 'selected' : ''}>Streaming</option>
          <option value="soundbar" ${this._builderProfile.device_type === 'soundbar' ? 'selected' : ''}>Soundbar</option>
          <option value="projector" ${this._builderProfile.device_type === 'projector' ? 'selected' : ''}>Projector</option>
          <option value="ac" ${this._builderProfile.device_type === 'ac' ? 'selected' : ''}>Air Conditioner</option>
        </select>
      </div>
      <div class="fg">
        <label class="fl">Icon</label>
        <input type="text" class="fi" id="grid-icon" value="${this._builderProfile.icon || 'mdi:remote'}" placeholder="mdi:remote">
      </div>
      <div class="fg">
        <label class="fl">Description</label>
        <textarea class="fi" id="grid-description" rows="2" placeholder="Optional description...">${this._builderProfile.description || ''}</textarea>
      </div>
      <div style="margin-top:16px;text-align:right;">
        <button class="btn btn-p" data-action="apply-grid-settings">
          <ha-icon icon="mdi:check"></ha-icon> Apply
        </button>
      </div>
    `;
    this._render();
  }

  _showIconPickerForBuilder() {
    // Show icon picker modal for builder button
    const currentIcon = this._builderSelectedButton 
      ? (this._builderProfile?.buttons?.find(b => b.id === this._builderSelectedButton)?.icon || '')
      : '';
    
    const iconCategories = {
      'Power & Control': [
        'mdi:power', 'mdi:power-off', 'mdi:power-standby', 'mdi:power-cycle', 'mdi:power-on',
        'mdi:play', 'mdi:pause', 'mdi:stop', 'mdi:play-pause', 'mdi:skip-next', 'mdi:skip-previous',
        'mdi:fast-forward', 'mdi:rewind', 'mdi:record', 'mdi:record-circle', 'mdi:eject',
      ],
      'Navigation': [
        'mdi:chevron-up', 'mdi:chevron-down', 'mdi:chevron-left', 'mdi:chevron-right',
        'mdi:arrow-up', 'mdi:arrow-down', 'mdi:arrow-left', 'mdi:arrow-right',
        'mdi:menu', 'mdi:menu-up', 'mdi:menu-down', 'mdi:menu-left', 'mdi:menu-right',
        'mdi:home', 'mdi:home-outline', 'mdi:arrow-left-circle', 'mdi:check', 'mdi:check-circle',
        'mdi:close', 'mdi:close-circle', 'mdi:dots-horizontal', 'mdi:dots-vertical',
      ],
      'Volume & Audio': [
        'mdi:volume-high', 'mdi:volume-medium', 'mdi:volume-low', 'mdi:volume-off', 'mdi:volume-mute',
        'mdi:volume-plus', 'mdi:volume-minus', 'mdi:speaker', 'mdi:speaker-wireless',
        'mdi:surround-sound', 'mdi:speaker-stereo', 'mdi:music', 'mdi:music-note',
        'mdi:microphone', 'mdi:microphone-off', 'mdi:headphones', 'mdi:radio',
      ],
      'Input & Source': [
        'mdi:hdmi-port', 'mdi:video-input-hdmi', 'mdi:usb', 'mdi:usb-port',
        'mdi:bluetooth', 'mdi:bluetooth-audio', 'mdi:wifi', 'mdi:antenna',
        'mdi:import', 'mdi:export', 'mdi:swap-horizontal', 'mdi:video-input-component',
        'mdi:toslink', 'mdi:audio-input-rca', 'mdi:cast', 'mdi:airplay',
      ],
      'Numbers': [
        'mdi:numeric-0', 'mdi:numeric-1', 'mdi:numeric-2', 'mdi:numeric-3', 'mdi:numeric-4',
        'mdi:numeric-5', 'mdi:numeric-6', 'mdi:numeric-7', 'mdi:numeric-8', 'mdi:numeric-9',
        'mdi:numeric-10', 'mdi:plus', 'mdi:minus', 'mdi:asterisk', 'mdi:pound',
      ],
      'Colors': [
        'mdi:circle', 'mdi:square', 'mdi:rectangle', 'mdi:triangle',
        'mdi:palette', 'mdi:format-color-fill', 'mdi:invert-colors',
      ],
      'TV & Video': [
        'mdi:television', 'mdi:television-classic', 'mdi:television-guide',
        'mdi:projector', 'mdi:projector-screen', 'mdi:movie', 'mdi:video',
        'mdi:youtube', 'mdi:netflix', 'mdi:amazon', 'mdi:hulu', 'mdi:plex',
        'mdi:aspect-ratio', 'mdi:fullscreen', 'mdi:picture-in-picture-bottom-right',
        'mdi:subtitles', 'mdi:closed-caption', 'mdi:information', 'mdi:help-circle',
      ],
      'Climate & Fan': [
        'mdi:fan', 'mdi:fan-off', 'mdi:fan-speed-1', 'mdi:fan-speed-2', 'mdi:fan-speed-3',
        'mdi:ceiling-fan', 'mdi:air-conditioner', 'mdi:thermometer', 'mdi:thermometer-plus', 'mdi:thermometer-minus',
        'mdi:snowflake', 'mdi:fire', 'mdi:water-percent', 'mdi:weather-windy',
        'mdi:arrow-oscillating', 'mdi:autorenew', 'mdi:timer', 'mdi:bed',
      ],
      'Lighting': [
        'mdi:lightbulb', 'mdi:lightbulb-outline', 'mdi:lightbulb-off', 'mdi:lightbulb-on',
        'mdi:lamp', 'mdi:ceiling-light', 'mdi:floor-lamp', 'mdi:led-strip',
        'mdi:brightness-5', 'mdi:brightness-6', 'mdi:brightness-7', 'mdi:white-balance-sunny',
      ],
      'Gaming': [
        'mdi:gamepad', 'mdi:gamepad-variant', 'mdi:controller-classic', 'mdi:nintendo-switch',
        'mdi:playstation', 'mdi:xbox', 'mdi:steam', 'mdi:controller',
      ],
      'Misc': [
        'mdi:cog', 'mdi:tune', 'mdi:wrench', 'mdi:heart', 'mdi:star', 'mdi:bookmark',
        'mdi:magnify', 'mdi:camera', 'mdi:image', 'mdi:sleep', 'mdi:alarm',
        'mdi:bell', 'mdi:email', 'mdi:phone', 'mdi:calendar', 'mdi:clock',
        'mdi:download', 'mdi:upload', 'mdi:refresh', 'mdi:sync', 'mdi:undo', 'mdi:redo',
      ],
    };
    
    this._modal = `
      <div class="modal-content" style="max-width:700px;max-height:90vh;overflow:hidden;display:flex;flex-direction:column;">
        <div class="modal-head">
          <h3><ha-icon icon="mdi:emoticon-outline"></ha-icon> Select Icon</h3>
          <button class="modal-close" data-action="close-modal">&times;</button>
        </div>
        
        <!-- Tabs -->
        <div style="display:flex;gap:4px;padding:0 16px;border-bottom:1px solid #333;">
          <button class="icon-tab active" data-tab="icons" style="padding:12px 16px;background:none;border:none;border-bottom:2px solid #3d5afe;color:#fff;cursor:pointer;">
            <ha-icon icon="mdi:emoticon-outline"></ha-icon> Icons
          </button>
          <button class="icon-tab" data-tab="upload" style="padding:12px 16px;background:none;border:none;border-bottom:2px solid transparent;color:#888;cursor:pointer;">
            <ha-icon icon="mdi:upload"></ha-icon> Upload Photo
          </button>
        </div>
        
        <!-- Icons Tab -->
        <div id="icons-tab" style="flex:1;overflow-y:auto;padding:16px;">
          <!-- Search -->
          <div style="margin-bottom:16px;">
            <input type="text" class="fi" id="icon-search" placeholder="Search icons (e.g., power, volume, play)..." style="width:100%;">
          </div>
          
          <!-- Icon Grid -->
          <div id="icon-grid">
            ${Object.entries(iconCategories).map(([category, icons]) => `
              <div class="icon-category" style="margin-bottom:20px;">
                <div style="font-size:13px;color:#888;margin-bottom:8px;font-weight:600;">${category}</div>
                <div style="display:flex;flex-wrap:wrap;gap:6px;">
                  ${icons.map(icon => `
                    <button class="icon-btn" data-icon="${icon}" type="button"
                            style="width:44px;height:44px;background:${currentIcon === icon ? '#3d5afe' : '#2a2a4a'};
                                   border:1px solid ${currentIcon === icon ? '#3d5afe' : '#444'};border-radius:8px;
                                   cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.15s;"
                            title="${icon}">
                      <ha-icon icon="${icon}" style="font-size:22px;color:${currentIcon === icon ? '#fff' : '#aaa'};"></ha-icon>
                    </button>
                  `).join('')}
                </div>
              </div>
            `).join('')}
          </div>
          
          <!-- Custom Icon Input -->
          <div style="margin-top:16px;padding-top:16px;border-top:1px solid #333;">
            <div style="font-size:13px;color:#888;margin-bottom:8px;">Custom MDI Icon</div>
            <div style="display:flex;gap:8px;">
              <input type="text" class="fi" id="custom-icon" placeholder="mdi:your-icon-name" value="${currentIcon}" style="flex:1;">
              <button class="btn btn-p" id="apply-custom-icon">Apply</button>
            </div>
            <div style="font-size:11px;color:#666;margin-top:4px;">
              Browse all icons at <a href="https://pictogrammers.com/library/mdi/" target="_blank" style="color:#64b5f6;">pictogrammers.com/library/mdi/</a>
            </div>
          </div>
        </div>
        
        <!-- Upload Tab -->
        <div id="upload-tab" style="display:none;flex:1;overflow-y:auto;padding:16px;">
          <div style="text-align:center;padding:20px;border:2px dashed #444;border-radius:12px;margin-bottom:16px;">
            <ha-icon icon="mdi:cloud-upload" style="font-size:48px;color:#666;"></ha-icon>
            <p style="color:#888;margin:12px 0;">Drag and drop an image or click to select</p>
            <input type="file" id="icon-upload" accept="image/*" style="display:none;">
            <button class="btn btn-p" id="upload-btn">Choose File</button>
          </div>
          
          <!-- Preview & Scale -->
          <div id="upload-preview" style="display:none;">
            <div style="text-align:center;margin-bottom:16px;">
              <div style="display:inline-block;padding:12px;background:#1a1a2e;border-radius:12px;">
                <img id="preview-img" style="max-width:200px;max-height:200px;border-radius:8px;">
              </div>
            </div>
            
            <div class="fg">
              <label class="fl">Button Size Preview</label>
              <div style="display:flex;gap:16px;justify-content:center;margin-top:8px;">
                <div style="text-align:center;">
                  <div style="width:50px;height:50px;background:#2a2a4a;border-radius:8px;display:flex;align-items:center;justify-content:center;overflow:hidden;">
                    <img id="preview-small" style="width:100%;height:100%;object-fit:cover;">
                  </div>
                  <div style="font-size:10px;color:#888;margin-top:4px;">Small</div>
                </div>
                <div style="text-align:center;">
                  <div style="width:70px;height:70px;background:#2a2a4a;border-radius:8px;display:flex;align-items:center;justify-content:center;overflow:hidden;">
                    <img id="preview-medium" style="width:100%;height:100%;object-fit:cover;">
                  </div>
                  <div style="font-size:10px;color:#888;margin-top:4px;">Medium</div>
                </div>
                <div style="text-align:center;">
                  <div style="width:100px;height:50px;background:#2a2a4a;border-radius:8px;display:flex;align-items:center;justify-content:center;overflow:hidden;">
                    <img id="preview-wide" style="width:100%;height:100%;object-fit:cover;">
                  </div>
                  <div style="font-size:10px;color:#888;margin-top:4px;">Wide (2x1)</div>
                </div>
              </div>
            </div>
            
            <div class="fg">
              <label class="fl">Scale & Crop</label>
              <input type="range" id="img-scale" min="50" max="200" value="100" style="width:100%;">
              <div style="display:flex;justify-content:space-between;font-size:11px;color:#888;">
                <span>50%</span>
                <span id="scale-value">100%</span>
                <span>200%</span>
              </div>
            </div>
            
            <div class="fg">
              <label class="fl">Output Size (px)</label>
              <select class="fi" id="output-size">
                <option value="48">48 x 48 (Small)</option>
                <option value="64" selected>64 x 64 (Standard)</option>
                <option value="96">96 x 96 (Large)</option>
                <option value="128">128 x 128 (HD)</option>
              </select>
            </div>
            
            <div style="display:flex;gap:8px;margin-top:16px;">
              <button class="btn btn-s" id="cancel-upload">Cancel</button>
              <button class="btn btn-p" id="apply-upload" style="flex:1;">
                <ha-icon icon="mdi:check"></ha-icon> Use This Image
              </button>
            </div>
          </div>
          
          <div style="margin-top:16px;padding:12px;background:#1a1a2e;border-radius:8px;">
            <div style="font-size:12px;color:#888;">
              <ha-icon icon="mdi:information" style="color:#64b5f6;"></ha-icon>
              <strong>Tips:</strong>
              <ul style="margin:8px 0 0 20px;padding:0;">
                <li>Square images work best</li>
                <li>Images are stored as Base64 in your profile</li>
                <li>Keep images under 100KB for best performance</li>
                <li>PNG with transparency is supported</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    `;
    
    this._render();
    
    // Set up event handlers
    setTimeout(() => {
      // Tab switching
      this.shadowRoot.querySelectorAll('.icon-tab').forEach(tab => {
        tab.addEventListener('click', () => {
          this.shadowRoot.querySelectorAll('.icon-tab').forEach(t => {
            t.classList.remove('active');
            t.style.borderBottomColor = 'transparent';
            t.style.color = '#888';
          });
          tab.classList.add('active');
          tab.style.borderBottomColor = '#3d5afe';
          tab.style.color = '#fff';
          
          const tabName = tab.dataset.tab;
          this.shadowRoot.getElementById('icons-tab').style.display = tabName === 'icons' ? 'block' : 'none';
          this.shadowRoot.getElementById('upload-tab').style.display = tabName === 'upload' ? 'block' : 'none';
        });
      });
      
      // Icon search
      const searchInput = this.shadowRoot.getElementById('icon-search');
      if (searchInput) {
        searchInput.addEventListener('input', (e) => {
          const query = e.target.value.toLowerCase();
          this.shadowRoot.querySelectorAll('.icon-btn').forEach(btn => {
            const icon = btn.dataset.icon.toLowerCase();
            btn.style.display = icon.includes(query) ? 'flex' : 'none';
          });
          this.shadowRoot.querySelectorAll('.icon-category').forEach(cat => {
            const visibleIcons = cat.querySelectorAll('.icon-btn[style*="display: flex"], .icon-btn:not([style*="display"])');
            cat.style.display = visibleIcons.length > 0 ? 'block' : 'none';
          });
        });
      }
      
      // Icon button clicks
      this.shadowRoot.querySelectorAll('.icon-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          this._applyIconToBuilder(btn.dataset.icon);
        });
      });
      
      // Custom icon apply
      const applyCustomBtn = this.shadowRoot.getElementById('apply-custom-icon');
      if (applyCustomBtn) {
        applyCustomBtn.addEventListener('click', () => {
          const icon = this.shadowRoot.getElementById('custom-icon')?.value;
          if (icon) {
            this._applyIconToBuilder(icon);
          }
        });
      }
      
      // File upload
      const uploadBtn = this.shadowRoot.getElementById('upload-btn');
      const fileInput = this.shadowRoot.getElementById('icon-upload');
      if (uploadBtn && fileInput) {
        uploadBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => {
          const file = e.target.files[0];
          if (file) {
            this._handleImageUpload(file);
          }
        });
      }
      
      // Scale slider
      const scaleSlider = this.shadowRoot.getElementById('img-scale');
      if (scaleSlider) {
        scaleSlider.addEventListener('input', (e) => {
          const scaleVal = this.shadowRoot.getElementById('scale-value');
          if (scaleVal) scaleVal.textContent = e.target.value + '%';
          this._updateImagePreviews();
        });
      }
      
      // Cancel upload
      const cancelBtn = this.shadowRoot.getElementById('cancel-upload');
      if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
          this.shadowRoot.getElementById('upload-preview').style.display = 'none';
          this._uploadedImage = null;
        });
      }
      
      // Apply upload
      const applyUploadBtn = this.shadowRoot.getElementById('apply-upload');
      if (applyUploadBtn) {
        applyUploadBtn.addEventListener('click', () => {
          this._applyUploadedImage();
        });
      }
    }, 100);
  }
  
  _handleImageUpload(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      this._uploadedImage = e.target.result;
      
      // Show preview
      const previewDiv = this.shadowRoot.getElementById('upload-preview');
      const previewImg = this.shadowRoot.getElementById('preview-img');
      
      if (previewDiv) previewDiv.style.display = 'block';
      if (previewImg) previewImg.src = this._uploadedImage;
      
      this._updateImagePreviews();
    };
    reader.readAsDataURL(file);
  }
  
  _updateImagePreviews() {
    if (!this._uploadedImage) return;
    
    const previewSmall = this.shadowRoot.getElementById('preview-small');
    const previewMedium = this.shadowRoot.getElementById('preview-medium');
    const previewWide = this.shadowRoot.getElementById('preview-wide');
    
    [previewSmall, previewMedium, previewWide].forEach(img => {
      if (img) img.src = this._uploadedImage;
    });
  }
  
  async _applyUploadedImage() {
    if (!this._uploadedImage) return;
    
    // Resize image to selected output size
    const outputSize = parseInt(this.shadowRoot.getElementById('output-size')?.value || '64');
    const scale = parseInt(this.shadowRoot.getElementById('img-scale')?.value || '100') / 100;
    
    try {
      const resizedImage = await this._resizeImage(this._uploadedImage, outputSize, scale);
      
      // Store as custom_image:base64data
      const imageData = `custom_image:${resizedImage}`;
      this._applyIconToBuilder(imageData);
    } catch (err) {
      console.error('[OmniRemote] Image resize error:', err);
      alert('Error processing image: ' + err.message);
    }
  }
  
  _resizeImage(dataUrl, size, scale) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d');
        
        // Calculate scaled dimensions
        const scaledSize = Math.min(img.width, img.height) / scale;
        const sx = (img.width - scaledSize) / 2;
        const sy = (img.height - scaledSize) / 2;
        
        // Draw centered and scaled
        ctx.drawImage(img, sx, sy, scaledSize, scaledSize, 0, 0, size, size);
        
        resolve(canvas.toDataURL('image/png', 0.9));
      };
      img.onerror = reject;
      img.src = dataUrl;
    });
  }
  
  _applyIconToBuilder(icon) {
    if (!this._builderSelectedButton || !this._builderProfile) return;
    
    const btn = this._builderProfile.buttons.find(b => b.id === this._builderSelectedButton);
    if (btn) {
      btn.icon = icon;
      this._modal = null;
      this._render();
      this._setupBuilderPropertyHandlers();
    }
  }
}

customElements.define('omniremote-panel', OmniRemotePanel);
