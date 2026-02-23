/**
 * OmniRemote Panel - Enhanced Edition
 * Full GUI for managing IR/RF remotes, rooms, devices, scenes, and projectors
 */

class OmniRemotePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._data = { rooms: [], devices: [], scenes: [], blasters: [], catalog: [], activities: [] };
    this._currentView = 'dashboard';
    this._selectedRoom = null;
    this._selectedDevice = null;
    this._selectedScene = null;
    this._selectedActivity = null;
    this._isLearning = false;
    this._learningCommand = null;
    this._catalogFilter = { brand: '', category: '' };
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) { this._init(); }
  }

  async _init() {
    this._initialized = true;
    this._render();
    await this._loadData();
  }

  async _loadData() {
    try {
      const [rooms, devices, scenes, blasters, catalog, activities] = await Promise.all([
        this._fetch('/api/omniremote/rooms'),
        this._fetch('/api/omniremote/devices'),
        this._fetch('/api/omniremote/scenes'),
        this._fetch('/api/omniremote/blasters'),
        this._fetch('/api/omniremote/catalog'),
        this._fetch('/api/omniremote/activities'),
      ]);
      this._data = {
        rooms: rooms.rooms || [],
        devices: devices.devices || [],
        scenes: scenes.scenes || [],
        blasters: blasters.blasters || [],
        catalog: catalog.devices || [],
        catalogBrands: catalog.brands || [],
        catalogCategories: catalog.categories || [],
        activities: activities.activities || [],
      };
      this._render();
    } catch (e) { console.error('Error loading data:', e); }
  }

  async _fetch(url, options = {}) {
    const r = await fetch(url, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers } });
    return r.json();
  }

  _render() {
    this.shadowRoot.innerHTML = `
      ${this._styles()}
      <div class="app">
        ${this._sidebar()}
        <main class="main">
          ${this._header()}
          <div class="content">${this._content()}</div>
        </main>
      </div>
      ${this._modal()}
      ${this._isLearning ? this._learning() : ''}
    `;
    this._events();
  }

  _styles() {
    return `<style>
      :host { display:block; height:100%; --c1:#03a9f4; --c2:#0288d1; --acc:#ff9800; --bg:#0f0f1a; --card:#1a1a2e; --card2:#252545; --txt:#e8e8e8; --txt2:#888; --brd:#2a2a4a; --ok:#4caf50; --err:#f44336; }
      * { box-sizing:border-box; }
      .app { display:flex; height:100vh; background:var(--bg); color:var(--txt); font-family:system-ui,sans-serif; }
      
      /* Sidebar */
      .sidebar { width:240px; background:var(--card); border-right:1px solid var(--brd); display:flex; flex-direction:column; }
      .sidebar-head { padding:16px; border-bottom:1px solid var(--brd); font-weight:600; display:flex; align-items:center; gap:8px; }
      .sidebar-head ha-icon { color:var(--c1); }
      .nav-section { padding:12px 0; border-bottom:1px solid var(--brd); }
      .nav-title { padding:4px 16px; font-size:10px; text-transform:uppercase; color:var(--txt2); letter-spacing:1px; }
      .nav-item { display:flex; align-items:center; gap:10px; padding:10px 16px; cursor:pointer; border-left:3px solid transparent; transition:all .15s; }
      .nav-item:hover { background:var(--card2); }
      .nav-item.active { background:var(--card2); border-left-color:var(--c1); }
      .nav-item ha-icon { color:var(--txt2); width:18px; }
      .nav-item.active ha-icon { color:var(--c1); }
      .nav-item .badge { margin-left:auto; background:var(--c1); padding:2px 7px; border-radius:10px; font-size:10px; }
      .room-list .nav-item { padding-left:28px; font-size:13px; }
      
      /* Main */
      .main { flex:1; display:flex; flex-direction:column; overflow:hidden; }
      .header { padding:14px 24px; border-bottom:1px solid var(--brd); display:flex; justify-content:space-between; align-items:center; background:var(--card); }
      .header h2 { margin:0; font-size:20px; font-weight:500; }
      .content { flex:1; padding:20px 24px; overflow-y:auto; }
      
      /* Buttons */
      .btn { padding:8px 14px; border:none; border-radius:6px; cursor:pointer; font-size:13px; display:inline-flex; align-items:center; gap:5px; transition:all .15s; }
      .btn-p { background:var(--c1); color:#fff; }
      .btn-p:hover { background:var(--c2); }
      .btn-s { background:var(--card2); color:var(--txt); border:1px solid var(--brd); }
      .btn-s:hover { background:#333355; }
      .btn-ok { background:var(--ok); color:#fff; }
      .btn-err { background:var(--err); color:#fff; }
      .btn-sm { padding:5px 10px; font-size:11px; }
      .btn-icon { width:32px; height:32px; padding:0; border-radius:6px; justify-content:center; }
      
      /* Cards */
      .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:16px; }
      .card { background:var(--card); border-radius:10px; padding:16px; border:1px solid var(--brd); transition:transform .15s,box-shadow .15s; }
      .card:hover { transform:translateY(-2px); box-shadow:0 6px 20px rgba(0,0,0,.3); }
      .card-head { display:flex; align-items:flex-start; gap:12px; margin-bottom:12px; }
      .card-icon { width:44px; height:44px; border-radius:10px; background:linear-gradient(135deg,var(--c1),var(--c2)); display:flex; align-items:center; justify-content:center; flex-shrink:0; }
      .card-icon ha-icon { color:#fff; }
      .card-icon.tv { background:linear-gradient(135deg,#e91e63,#c2185b); }
      .card-icon.projector { background:linear-gradient(135deg,#3f51b5,#303f9f); }
      .card-icon.receiver { background:linear-gradient(135deg,#9c27b0,#7b1fa2); }
      .card-icon.streaming { background:linear-gradient(135deg,#673ab7,#512da8); }
      .card-icon.scene { background:linear-gradient(135deg,#ff9800,#f57c00); }
      .card-info { flex:1; min-width:0; }
      .card-title { font-size:15px; font-weight:600; }
      .card-sub { font-size:12px; color:var(--txt2); margin-top:2px; }
      .card-status { display:flex; align-items:center; gap:6px; margin:10px 0; padding:8px; background:var(--bg); border-radius:6px; font-size:12px; }
      .dot { width:8px; height:8px; border-radius:50%; background:var(--err); }
      .dot.on { background:var(--ok); }
      .card-actions { display:flex; gap:6px; flex-wrap:wrap; margin-top:12px; }
      
      /* Stats */
      .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:12px; margin-bottom:20px; }
      .stat { background:var(--card); border-radius:10px; padding:16px; border:1px solid var(--brd); text-align:center; }
      .stat-val { font-size:28px; font-weight:700; background:linear-gradient(135deg,var(--c1),#00bcd4); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
      .stat-lbl { font-size:11px; color:var(--txt2); margin-top:4px; }
      
      /* Quick Scenes */
      .scenes-row { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:20px; }
      .scene-btn { background:linear-gradient(135deg,var(--card),var(--card2)); border:1px solid var(--brd); border-radius:10px; padding:12px 20px; cursor:pointer; display:flex; align-items:center; gap:10px; transition:all .15s; }
      .scene-btn:hover { transform:scale(1.02); border-color:var(--c1); box-shadow:0 4px 15px rgba(3,169,244,.2); }
      .scene-btn:active { transform:scale(.98); }
      .scene-btn ha-icon { color:var(--acc); }
      
      /* Section */
      .section { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
      .section h3 { margin:0; font-size:14px; font-weight:600; }
      
      /* Control Panel */
      .ctrl { background:var(--card); border-radius:12px; padding:20px; border:1px solid var(--brd); }
      .ctrl-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid var(--brd); }
      .pwr-toggle { width:50px; height:26px; border-radius:13px; background:var(--err); cursor:pointer; position:relative; transition:background .2s; }
      .pwr-toggle.on { background:var(--ok); }
      .pwr-toggle::after { content:''; position:absolute; width:20px; height:20px; background:#fff; border-radius:50%; top:3px; left:3px; transition:transform .2s; }
      .pwr-toggle.on::after { transform:translateX(24px); }
      
      /* Input Grid */
      .inputs { display:grid; grid-template-columns:repeat(auto-fill,minmax(90px,1fr)); gap:8px; margin:16px 0; }
      .input-btn { padding:10px 8px; background:var(--bg); border:2px solid var(--brd); border-radius:8px; color:var(--txt); cursor:pointer; text-align:center; font-size:11px; transition:all .15s; }
      .input-btn:hover { border-color:var(--c1); }
      .input-btn.active { background:var(--c1); border-color:var(--c1); color:#fff; }
      
      /* Remote Pad */
      .pad { display:flex; flex-direction:column; align-items:center; gap:8px; margin:16px 0; }
      .pad-row { display:flex; gap:8px; }
      .pad-btn { width:44px; height:44px; border-radius:10px; background:var(--bg); border:1px solid var(--brd); color:var(--txt); cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all .12s; }
      .pad-btn:hover { background:var(--c1); border-color:var(--c1); }
      .pad-btn:active { transform:scale(.9); }
      .pad-btn.ok { width:60px; height:60px; border-radius:50%; }
      
      /* Commands */
      .cmds { margin-top:16px; }
      .cmds h4 { margin:0 0 10px; font-size:11px; color:var(--txt2); text-transform:uppercase; letter-spacing:1px; }
      .cmd-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(70px,1fr)); gap:6px; }
      .cmd-btn { padding:8px 6px; background:var(--bg); border:1px solid var(--brd); border-radius:6px; color:var(--txt); cursor:pointer; text-align:center; font-size:10px; word-break:break-word; transition:all .12s; }
      .cmd-btn:hover { background:var(--c1); border-color:var(--c1); }
      .cmd-btn:active { transform:scale(.95); }
      
      /* Projector */
      .proj-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin:12px 0; }
      .proj-stat { background:var(--bg); padding:12px; border-radius:8px; text-align:center; }
      .proj-stat .v { font-size:20px; font-weight:600; color:var(--c1); }
      .proj-stat .l { font-size:10px; color:var(--txt2); margin-top:3px; }
      
      /* Modal */
      .modal-bg { position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,.75); display:flex; align-items:center; justify-content:center; z-index:1000; }
      .modal { background:var(--card); border-radius:12px; padding:20px; width:90%; max-width:550px; max-height:85vh; overflow-y:auto; border:1px solid var(--brd); }
      .modal-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid var(--brd); }
      .modal-head h3 { margin:0; font-size:18px; }
      .modal-x { background:none; border:none; color:var(--txt2); cursor:pointer; font-size:24px; line-height:1; }
      .modal-x:hover { color:var(--txt); }
      
      /* Forms */
      .fg { margin-bottom:14px; }
      .fl { display:block; margin-bottom:6px; font-size:12px; color:var(--txt2); }
      .fi, .fs { width:100%; padding:10px 12px; border:1px solid var(--brd); border-radius:6px; background:var(--bg); color:var(--txt); font-size:13px; }
      .fi:focus, .fs:focus { outline:none; border-color:var(--c1); }
      .fr { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
      
      /* Timeline */
      .tl { background:var(--bg); border-radius:10px; padding:14px; margin:12px 0; }
      .tl-item { display:flex; align-items:center; gap:12px; padding:12px; background:var(--card); border-radius:8px; margin-bottom:8px; border:1px solid var(--brd); }
      .tl-num { width:28px; height:28px; border-radius:50%; background:var(--c1); display:flex; align-items:center; justify-content:center; font-weight:600; font-size:12px; flex-shrink:0; }
      .tl-content { flex:1; display:flex; gap:8px; flex-wrap:wrap; }
      .tl-content select { flex:1; min-width:100px; }
      .tl-delay { display:flex; align-items:center; gap:6px; color:var(--txt2); font-size:12px; }
      .tl-delay input { width:50px; }
      
      /* Learning */
      .learn-bg { position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,.9); display:flex; flex-direction:column; align-items:center; justify-content:center; z-index:2000; }
      .learn-pulse { width:100px; height:100px; border-radius:50%; background:var(--c1); animation:pulse 1.5s infinite; display:flex; align-items:center; justify-content:center; box-shadow:0 0 50px rgba(3,169,244,.5); }
      .learn-pulse ha-icon { color:#fff; --mdc-icon-size:40px; }
      @keyframes pulse { 0%,100% { transform:scale(1); } 50% { transform:scale(1.1); } }
      .learn-txt { margin-top:24px; font-size:18px; }
      .learn-sub { margin-top:8px; color:var(--txt2); }
      
      /* Empty */
      .empty { text-align:center; padding:50px 20px; color:var(--txt2); }
      .empty ha-icon { --mdc-icon-size:48px; opacity:.4; margin-bottom:16px; }
      .empty h3 { color:var(--txt); margin-bottom:8px; }
      
      @media (max-width:768px) { .sidebar { width:180px; } .fr { grid-template-columns:1fr; } }
    </style>`;
  }

  _sidebar() {
    return `
      <aside class="sidebar">
        <div class="sidebar-head"><ha-icon icon="mdi:remote-tv"></ha-icon> OmniRemote</div>
        <div class="nav-section">
          <div class="nav-title">Main</div>
          <div class="nav-item ${this._currentView==='dashboard'?'active':''}" data-view="dashboard"><ha-icon icon="mdi:view-dashboard"></ha-icon>Dashboard</div>
          <div class="nav-item ${this._currentView==='devices'?'active':''}" data-view="devices"><ha-icon icon="mdi:devices"></ha-icon>Devices<span class="badge">${this._data.devices.length}</span></div>
          <div class="nav-item ${this._currentView==='activities'?'active':''}" data-view="activities"><ha-icon icon="mdi:play-box-multiple"></ha-icon>Activities<span class="badge">${this._data.activities?.length||0}</span></div>
          <div class="nav-item ${this._currentView==='scenes'?'active':''}" data-view="scenes"><ha-icon icon="mdi:movie-open"></ha-icon>Scenes<span class="badge">${this._data.scenes.length}</span></div>
        </div>
        <div class="nav-section">
          <div class="nav-title">Rooms</div>
          <div class="room-list">
            ${this._data.rooms.map(r=>`<div class="nav-item ${this._currentView==='room'&&this._selectedRoom===r.id?'active':''}" data-view="room" data-room-id="${r.id}"><ha-icon icon="${r.icon||'mdi:sofa'}"></ha-icon>${r.name}</div>`).join('')}
            <div class="nav-item" data-action="add-room" style="color:var(--c1);"><ha-icon icon="mdi:plus"></ha-icon>Add Room</div>
          </div>
        </div>
        <div class="nav-section">
          <div class="nav-title">Setup</div>
          <div class="nav-item ${this._currentView==='catalog'?'active':''}" data-view="catalog"><ha-icon icon="mdi:book-open-variant"></ha-icon>Device Catalog</div>
          <div class="nav-item ${this._currentView==='blasters'?'active':''}" data-view="blasters"><ha-icon icon="mdi:access-point"></ha-icon>Blasters<span class="badge">${this._data.blasters.length}</span></div>
          <div class="nav-item ${this._currentView==='import'?'active':''}" data-view="import"><ha-icon icon="mdi:import"></ha-icon>Import/Export</div>
        </div>
      </aside>`;
  }

  _header() {
    const t = { dashboard:'Dashboard', devices:'All Devices', scenes:'Scenes', activities:'Activities', catalog:'Device Catalog', room:this._data.rooms.find(r=>r.id===this._selectedRoom)?.name||'Room', blasters:'Blasters', import:'Import/Export', device:this._data.devices.find(d=>d.id===this._selectedDevice)?.name||'Device' };
    let btns = '';
    if (this._currentView==='devices') btns = `<button class="btn btn-p" data-action="add-device"><ha-icon icon="mdi:plus"></ha-icon>Add Device</button>`;
    if (this._currentView==='activities') btns = `<button class="btn btn-p" data-action="add-activity"><ha-icon icon="mdi:plus"></ha-icon>Create Activity</button>`;
    if (this._currentView==='scenes') btns = `<button class="btn btn-p" data-action="add-scene"><ha-icon icon="mdi:plus"></ha-icon>Create Scene</button>`;
    if (this._currentView==='blasters') btns = `<button class="btn btn-p" data-action="discover"><ha-icon icon="mdi:magnify"></ha-icon>Discover</button>`;
    if (this._currentView==='device') btns = `<button class="btn btn-s" data-action="learn-device" data-device-id="${this._selectedDevice}"><ha-icon icon="mdi:record"></ha-icon>Learn</button><button class="btn btn-s" data-action="edit-device" data-device-id="${this._selectedDevice}"><ha-icon icon="mdi:pencil"></ha-icon>Edit</button>`;
    return `<header class="header"><h2>${t[this._currentView]||'Dashboard'}</h2><div>${btns}</div></header>`;
  }

  _content() {
    switch(this._currentView) {
      case 'dashboard': return this._dashboard();
      case 'devices': return this._devices();
      case 'scenes': return this._scenes();
      case 'activities': return this._activities();
      case 'catalog': return this._catalog();
      case 'room': return this._room();
      case 'blasters': return this._blasters();
      case 'import': return this._import();
      case 'device': return this._deviceCtrl();
      default: return this._dashboard();
    }
  }

  _dashboard() {
    const cmds = this._data.devices.reduce((s,d)=>s+Object.keys(d.commands||{}).length,0);
    const on = this._data.devices.filter(d=>d.power_state).length;
    return `
      <div class="stats">
        <div class="stat"><div class="stat-val">${this._data.rooms.length}</div><div class="stat-lbl">Rooms</div></div>
        <div class="stat"><div class="stat-val">${this._data.devices.length}</div><div class="stat-lbl">Devices</div></div>
        <div class="stat"><div class="stat-val">${on}</div><div class="stat-lbl">Active</div></div>
        <div class="stat"><div class="stat-val">${cmds}</div><div class="stat-lbl">Commands</div></div>
        <div class="stat"><div class="stat-val">${this._data.scenes.length}</div><div class="stat-lbl">Scenes</div></div>
      </div>
      ${this._data.scenes.length?`<div class="section"><h3>Quick Scenes</h3></div><div class="scenes-row">${this._data.scenes.map(s=>`<div class="scene-btn" data-action="run-scene" data-scene-id="${s.id}"><ha-icon icon="${s.icon||'mdi:play'}"></ha-icon>${s.name}</div>`).join('')}</div>`:''}
      <div class="section"><h3>Devices</h3></div>
      <div class="grid">${this._data.devices.slice(0,6).map(d=>this._deviceCard(d)).join('')}${!this._data.devices.length?`<div class="empty"><ha-icon icon="mdi:devices"></ha-icon><h3>No Devices</h3><p>Add your first device</p><button class="btn btn-p" data-action="add-device">Add Device</button></div>`:''}</div>`;
  }

  _devices() {
    if (!this._data.devices.length) return `<div class="empty"><ha-icon icon="mdi:devices"></ha-icon><h3>No Devices</h3><p>Add devices to control</p><button class="btn btn-p" data-action="add-device">Add Device</button></div>`;
    return `<div class="grid">${this._data.devices.map(d=>this._deviceCard(d)).join('')}</div>`;
  }

  _deviceCard(d) {
    const room = this._data.rooms.find(r=>r.id===d.room_id);
    const cmds = Object.keys(d.commands||{}).length;
    return `
      <div class="card">
        <div class="card-head">
          <div class="card-icon ${d.category||''}"><ha-icon icon="${this._catIcon(d.category)}"></ha-icon></div>
          <div class="card-info"><div class="card-title">${d.name}</div><div class="card-sub">${d.brand||''} ${room?'• '+room.name:''}</div></div>
        </div>
        <div class="card-status"><span class="dot ${d.power_state?'on':''}"></span>${d.power_state?'On':'Off'}${d.current_input?`<span style="margin-left:auto">${d.current_input}</span>`:''}</div>
        <div class="card-sub">${cmds} commands</div>
        <div class="card-actions">
          <button class="btn btn-p btn-sm" data-action="open-device" data-device-id="${d.id}"><ha-icon icon="mdi:remote"></ha-icon>Control</button>
          <button class="btn btn-s btn-sm btn-icon" data-action="toggle-power" data-device-id="${d.id}"><ha-icon icon="mdi:power"></ha-icon></button>
          <button class="btn btn-s btn-sm btn-icon" data-action="edit-device" data-device-id="${d.id}"><ha-icon icon="mdi:pencil"></ha-icon></button>
        </div>
      </div>`;
  }

  _room() {
    const room = this._data.rooms.find(r=>r.id===this._selectedRoom);
    if (!room) return '<p>Room not found</p>';
    const devs = this._data.devices.filter(d=>d.room_id===room.id);
    const scenes = this._data.scenes.filter(s=>s.room_id===room.id);
    return `
      ${scenes.length?`<div class="section"><h3>Room Scenes</h3></div><div class="scenes-row">${scenes.map(s=>`<div class="scene-btn" data-action="run-scene" data-scene-id="${s.id}"><ha-icon icon="${s.icon||'mdi:play'}"></ha-icon>${s.name}</div>`).join('')}</div>`:''}
      <div class="section"><h3>Devices in ${room.name}</h3></div>
      <div class="grid">${devs.map(d=>this._deviceCard(d)).join('')}${!devs.length?'<div class="empty"><ha-icon icon="mdi:devices"></ha-icon><h3>No Devices</h3><button class="btn btn-p" data-action="add-device">Add Device</button></div>':''}</div>`;
  }

  _deviceCtrl() {
    const d = this._data.devices.find(x=>x.id===this._selectedDevice);
    if (!d) return '<p>Device not found</p>';
    const cmds = Object.keys(d.commands||{});
    const isProj = d.category==='projector';
    const pwr = cmds.filter(c=>c.match(/power|^on$|^off$/i));
    const inp = cmds.filter(c=>c.match(/input|hdmi|source/i));
    const nav = cmds.filter(c=>['up','down','left','right','ok','enter','select','back','menu','home'].includes(c.toLowerCase()));
    const vol = cmds.filter(c=>c.match(/volume|mute/i));
    const other = cmds.filter(c=>!pwr.includes(c)&&!inp.includes(c)&&!nav.includes(c)&&!vol.includes(c));
    
    return `
      <div class="ctrl">
        <div class="ctrl-head">
          <div style="display:flex;align-items:center;gap:12px;">
            <div class="card-icon ${d.category}"><ha-icon icon="${this._catIcon(d.category)}"></ha-icon></div>
            <div><div style="font-size:16px;font-weight:600;">${d.name}</div><div style="font-size:12px;color:var(--txt2);">${d.brand||''} ${d.model||''}</div></div>
          </div>
          <div class="pwr-toggle ${d.power_state?'on':''}" data-action="toggle-power" data-device-id="${d.id}"></div>
        </div>
        ${isProj?`<div class="proj-stats"><div class="proj-stat"><div class="v">${d.lamp_hours||'—'}</div><div class="l">Lamp Hours</div></div><div class="proj-stat"><div class="v">${d.current_input||'—'}</div><div class="l">Input</div></div><div class="proj-stat"><div class="v">${d.lens_position||'Home'}</div><div class="l">Lens</div></div></div>`:''}
        ${inp.length?`<div class="cmds"><h4>Inputs</h4><div class="inputs">${inp.map(c=>`<button class="input-btn ${d.current_input===c?'active':''}" data-action="send-cmd" data-device-id="${d.id}" data-command="${c}">${c.replace(/_/g,' ').replace(/input/i,'')}</button>`).join('')}</div></div>`:''}
        ${nav.length>=4?`<div class="cmds"><h4>Navigation</h4><div class="pad"><div class="pad-row">${nav.includes('up')?`<button class="pad-btn" data-action="send-cmd" data-device-id="${d.id}" data-command="up"><ha-icon icon="mdi:chevron-up"></ha-icon></button>`:''}</div><div class="pad-row">${nav.includes('left')?`<button class="pad-btn" data-action="send-cmd" data-device-id="${d.id}" data-command="left"><ha-icon icon="mdi:chevron-left"></ha-icon></button>`:''}${nav.some(c=>['ok','enter','select'].includes(c.toLowerCase()))?`<button class="pad-btn ok" data-action="send-cmd" data-device-id="${d.id}" data-command="${nav.find(c=>['ok','enter','select'].includes(c.toLowerCase()))}">OK</button>`:''}${nav.includes('right')?`<button class="pad-btn" data-action="send-cmd" data-device-id="${d.id}" data-command="right"><ha-icon icon="mdi:chevron-right"></ha-icon></button>`:''}</div><div class="pad-row">${nav.includes('down')?`<button class="pad-btn" data-action="send-cmd" data-device-id="${d.id}" data-command="down"><ha-icon icon="mdi:chevron-down"></ha-icon></button>`:''}</div><div class="pad-row" style="margin-top:8px;">${nav.includes('back')?`<button class="pad-btn" data-action="send-cmd" data-device-id="${d.id}" data-command="back"><ha-icon icon="mdi:arrow-left"></ha-icon></button>`:''}${nav.includes('home')?`<button class="pad-btn" data-action="send-cmd" data-device-id="${d.id}" data-command="home"><ha-icon icon="mdi:home"></ha-icon></button>`:''}${nav.includes('menu')?`<button class="pad-btn" data-action="send-cmd" data-device-id="${d.id}" data-command="menu"><ha-icon icon="mdi:menu"></ha-icon></button>`:''}</div></div></div>`:''}
        ${vol.length?`<div class="cmds"><h4>Volume</h4><div class="cmd-grid">${vol.map(c=>`<button class="cmd-btn" data-action="send-cmd" data-device-id="${d.id}" data-command="${c}">${c.replace(/_/g,' ')}</button>`).join('')}</div></div>`:''}
        ${other.length?`<div class="cmds"><h4>All Commands</h4><div class="cmd-grid">${other.map(c=>`<button class="cmd-btn" data-action="send-cmd" data-device-id="${d.id}" data-command="${c}">${c.replace(/_/g,' ')}</button>`).join('')}</div></div>`:''}
        ${!cmds.length?`<div class="empty"><ha-icon icon="mdi:remote"></ha-icon><h3>No Commands</h3><p>Learn commands from your remote</p><button class="btn btn-p" data-action="learn-device" data-device-id="${d.id}">Learn Commands</button></div>`:''}
      </div>`;
  }

  _scenes() {
    if (!this._data.scenes.length) return `<div class="empty"><ha-icon icon="mdi:movie-open"></ha-icon><h3>No Scenes</h3><p>Create scenes to control multiple devices</p><button class="btn btn-p" data-action="add-scene">Create Scene</button></div>`;
    return `<div class="grid">${this._data.scenes.map(s=>`
      <div class="card">
        <div class="card-head"><div class="card-icon scene"><ha-icon icon="${s.icon||'mdi:play'}"></ha-icon></div><div class="card-info"><div class="card-title">${s.name}</div><div class="card-sub">${(s.actions||[]).length} actions</div></div></div>
        <div class="card-actions">
          <button class="btn btn-ok" data-action="run-scene" data-scene-id="${s.id}"><ha-icon icon="mdi:play"></ha-icon>Run</button>
          <button class="btn btn-s btn-icon" data-action="edit-scene" data-scene-id="${s.id}"><ha-icon icon="mdi:pencil"></ha-icon></button>
          <button class="btn btn-err btn-icon" data-action="delete-scene" data-scene-id="${s.id}"><ha-icon icon="mdi:delete"></ha-icon></button>
        </div>
      </div>`).join('')}</div>`;
  }

  _catalog() {
    const devices = this._data.catalog || [];
    const brands = this._data.catalogBrands || [];
    
    return `
      <div style="margin-bottom:20px;">
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
          <select class="fs" id="catalog-brand" style="width:auto;min-width:150px;">
            <option value="">All Brands</option>
            ${brands.map(b=>`<option value="${b}">${b}</option>`).join('')}
          </select>
          <select class="fs" id="catalog-category" style="width:auto;min-width:150px;">
            <option value="">All Categories</option>
            <option value="tv">TVs</option>
            <option value="projector">Projectors</option>
            <option value="receiver">Receivers</option>
            <option value="streaming">Streaming</option>
            <option value="fan">Fans</option>
            <option value="light">Lights</option>
          </select>
        </div>
      </div>
      <div class="grid">
        ${devices.map(d=>`
          <div class="card">
            <div class="card-head">
              <div class="card-icon ${d.category}"><ha-icon icon="${this._catIcon(d.category)}"></ha-icon></div>
              <div class="card-info">
                <div class="card-title">${d.name}</div>
                <div class="card-sub">${d.brand} • ${Object.keys(d.ir_codes||{}).length} IR codes</div>
              </div>
            </div>
            <div style="font-size:11px;color:var(--txt2);margin:8px 0;">
              Control: ${d.control_methods?.join(', ')||'IR'}
            </div>
            ${d.apps && Object.keys(d.apps).length ? `<div style="font-size:11px;color:var(--txt2);">${Object.keys(d.apps).length} pre-configured apps</div>` : ''}
            <div class="card-actions">
              <button class="btn btn-p btn-sm" data-action="add-from-catalog" data-catalog-id="${d.id}">
                <ha-icon icon="mdi:plus"></ha-icon>Add to My Devices
              </button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  _activities() {
    const activities = this._data.activities || [];
    
    if (!activities.length) {
      return `
        <div class="empty">
          <ha-icon icon="mdi:play-box-multiple"></ha-icon>
          <h3>No Activities</h3>
          <p>Activities are powerful macros that control multiple devices.<br>Examples: "Watch Roku", "Gaming", "Movie Night"</p>
          <button class="btn btn-p" data-action="add-activity">Create Activity</button>
        </div>
        <div style="margin-top:30px;">
          <h3>Quick Start Templates</h3>
          <div class="grid" style="margin-top:15px;">
            <div class="card">
              <div class="card-head">
                <div class="card-icon streaming"><ha-icon icon="mdi:roku"></ha-icon></div>
                <div class="card-info"><div class="card-title">Watch Roku</div><div class="card-sub">Power on TV, set input, launch app</div></div>
              </div>
              <div class="card-actions"><button class="btn btn-p btn-sm" data-action="create-template" data-template="watch_roku">Use Template</button></div>
            </div>
            <div class="card">
              <div class="card-head">
                <div class="card-icon projector"><ha-icon icon="mdi:projector"></ha-icon></div>
                <div class="card-info"><div class="card-title">Watch Projector</div><div class="card-sub">Lower screen, warm up projector, set inputs</div></div>
              </div>
              <div class="card-actions"><button class="btn btn-p btn-sm" data-action="create-template" data-template="watch_projector">Use Template</button></div>
            </div>
            <div class="card">
              <div class="card-head">
                <div class="card-icon"><ha-icon icon="mdi:controller"></ha-icon></div>
                <div class="card-info"><div class="card-title">Gaming</div><div class="card-sub">TV game mode, power console, set receiver</div></div>
              </div>
              <div class="card-actions"><button class="btn btn-p btn-sm" data-action="create-template" data-template="gaming">Use Template</button></div>
            </div>
          </div>
        </div>
      `;
    }
    
    return `
      <div class="grid">
        ${activities.map(a=>`
          <div class="card">
            <div class="card-head">
              <div class="card-icon scene"><ha-icon icon="${a.icon||'mdi:play'}"></ha-icon></div>
              <div class="card-info">
                <div class="card-title">${a.name}</div>
                <div class="card-sub">${(a.actions||[]).length} actions • ${a.category||'General'}</div>
              </div>
            </div>
            ${a.description?`<div style="font-size:12px;color:var(--txt2);margin:8px 0;">${a.description}</div>`:''}
            <div class="card-actions">
              <button class="btn btn-ok" data-action="run-activity" data-activity-id="${a.id}"><ha-icon icon="mdi:play"></ha-icon>Start</button>
              <button class="btn btn-s btn-icon" data-action="edit-activity" data-activity-id="${a.id}"><ha-icon icon="mdi:pencil"></ha-icon></button>
              <button class="btn btn-err btn-icon" data-action="delete-activity" data-activity-id="${a.id}"><ha-icon icon="mdi:delete"></ha-icon></button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  _blasters() {
    return `<div class="grid">${this._data.blasters.map(b=>`<div class="card"><div class="card-head"><div class="card-icon"><ha-icon icon="mdi:access-point"></ha-icon></div><div class="card-info"><div class="card-title">${b.name}</div><div class="card-sub">${b.host} • ${b.mac}</div></div></div></div>`).join('')}${!this._data.blasters.length?`<div class="empty"><ha-icon icon="mdi:access-point"></ha-icon><h3>No Blasters</h3><p>Click Discover to find devices</p><button class="btn btn-p" data-action="discover">Discover</button></div>`:''}</div>`;
  }

  _import() {
    return `
      <div class="card" style="max-width:500px;"><h3 style="margin-top:0;">Import Flipper Zero Files</h3><div class="fg"><label class="fl">Path to .ir/.sub files</label><input type="text" class="fi" id="import-path" placeholder="/config/flipper/infrared"></div><button class="btn btn-p" data-action="import"><ha-icon icon="mdi:import"></ha-icon>Import</button></div>
      <div class="card" style="max-width:500px;margin-top:16px;"><h3 style="margin-top:0;">Export to Flipper</h3><div class="fg"><label class="fl">Export path</label><input type="text" class="fi" id="export-path" placeholder="/config/flipper_export"></div><button class="btn btn-s" data-action="export"><ha-icon icon="mdi:export"></ha-icon>Export</button></div>`;
  }

  _modal() {
    if (!this._modalContent) return '';
    return `<div class="modal-bg" data-action="close-modal"><div class="modal" onclick="event.stopPropagation()">${this._modalContent}</div></div>`;
  }

  _learning() {
    return `<div class="learn-bg"><div class="learn-pulse"><ha-icon icon="mdi:remote"></ha-icon></div><div class="learn-txt">Learning: ${this._learningCommand||'Command'}</div><div class="learn-sub">Press button on your remote...</div><button class="btn btn-s" style="margin-top:30px;" data-action="cancel-learn">Cancel</button></div>`;
  }

  _catIcon(c) {
    const m = { tv:'mdi:television', projector:'mdi:projector', receiver:'mdi:speaker', soundbar:'mdi:soundbar', streaming:'mdi:cast', cable_box:'mdi:set-top-box', ac:'mdi:air-conditioner', fan:'mdi:fan', light:'mdi:lightbulb' };
    return m[c]||'mdi:remote';
  }

  _events() {
    this.shadowRoot.querySelectorAll('[data-view]').forEach(e=>e.addEventListener('click',()=>{
      this._currentView=e.dataset.view;
      if(e.dataset.roomId) this._selectedRoom=e.dataset.roomId;
      this._render();
    }));
    this.shadowRoot.querySelectorAll('[data-action]').forEach(e=>e.addEventListener('click',ev=>this._action(ev)));
  }

  async _action(e) {
    const a=e.currentTarget.dataset.action, id=e.currentTarget.dataset.deviceId||e.currentTarget.dataset.sceneId||e.currentTarget.dataset.roomId;
    switch(a) {
      case 'add-room': this._addRoomModal(); break;
      case 'add-device': this._addDeviceModal(); break;
      case 'add-scene': this._addSceneModal(); break;
      case 'open-device': this._selectedDevice=id; this._currentView='device'; this._render(); break;
      case 'toggle-power': await this._togglePower(id); break;
      case 'send-cmd': 
        await this._sendCmd(e.currentTarget.dataset.deviceId, e.currentTarget.dataset.command);
        e.currentTarget.style.background='var(--ok)';
        setTimeout(()=>e.currentTarget.style.background='',150);
        break;
      case 'learn-device': this._learnModal(id); break;
      case 'edit-device': this._editDeviceModal(id); break;
      case 'edit-scene': this._editSceneModal(id); break;
      case 'run-scene': await this._runScene(id); break;
      case 'delete-scene': if(confirm('Delete?')){await this._fetch('/api/omniremote/scenes',{method:'DELETE',body:JSON.stringify({id})});await this._loadData();} break;
      case 'discover': await this._fetch('/api/omniremote/blasters',{method:'POST'}); await this._loadData(); break;
      case 'import': const p=this.shadowRoot.getElementById('import-path').value; if(p)this._hass.callService('omniremote','import_flipper',{path:p}); alert('Importing...'); setTimeout(()=>this._loadData(),2000); break;
      case 'close-modal': this._modalContent=null; this._render(); break;
      case 'cancel-learn': this._isLearning=false; this._render(); break;
      case 'save-room': await this._saveRoom(); break;
      case 'save-device': await this._saveDevice(); break;
      case 'save-scene': await this._saveScene(); break;
      case 'start-learn': await this._startLearn(); break;
      // Catalog actions
      case 'add-from-catalog': await this._addFromCatalog(e.currentTarget.dataset.catalogId); break;
      // Activity actions
      case 'add-activity': this._addActivityModal(); break;
      case 'run-activity': await this._runActivity(e.currentTarget.dataset.activityId); break;
      case 'delete-activity': if(confirm('Delete activity?')){await this._fetch('/api/omniremote/activities',{method:'DELETE',body:JSON.stringify({id:e.currentTarget.dataset.activityId})});await this._loadData();} break;
      case 'create-template': await this._createFromTemplate(e.currentTarget.dataset.template); break;
    }
  }

  async _addFromCatalog(catalogId) {
    const roomId = this._data.rooms[0]?.id || null;
    const result = await this._fetch('/api/omniremote/catalog', {
      method: 'POST',
      body: JSON.stringify({ catalog_id: catalogId, room_id: roomId })
    });
    if (result.device) {
      alert(`Added ${result.device.name} with ${result.commands_added} commands!`);
      await this._loadData();
    }
  }

  async _runActivity(activityId) {
    await this._fetch('/api/omniremote/activities', {
      method: 'POST',
      body: JSON.stringify({ action: 'run', activity_id: activityId })
    });
  }

  async _createFromTemplate(template) {
    // Would need to show a modal to configure the template
    const devices = this._data.devices;
    const tvDevice = devices.find(d => d.category === 'tv');
    const receiverDevice = devices.find(d => d.category === 'receiver');
    const streamingDevice = devices.find(d => d.category === 'streaming');
    
    if (!tvDevice) {
      alert('Please add a TV device first');
      return;
    }
    
    const params = {
      name: template === 'watch_roku' ? 'Watch Roku' : template === 'watch_projector' ? 'Movie Night' : 'Gaming',
      tv_device_id: tvDevice.id,
    };
    
    if (receiverDevice) params.receiver_device_id = receiverDevice.id;
    if (streamingDevice && template === 'watch_roku') params.roku_device_id = streamingDevice.id;
    
    await this._fetch('/api/omniremote/activities', {
      method: 'POST',
      body: JSON.stringify({ action: 'create_from_template', template, params })
    });
    
    await this._loadData();
    alert('Activity created!');
  }

  _addActivityModal() {
    this._modalContent = `
      <div class="modal-head"><h3>Create Activity</h3><button class="modal-x" data-action="close-modal">&times;</button></div>
      <div class="fg"><label class="fl">Activity Name</label><input class="fi" id="activity-name" placeholder="Watch Roku"></div>
      <div class="fg"><label class="fl">Icon</label><input class="fi" id="activity-icon" value="mdi:play"></div>
      <div class="fg"><label class="fl">Category</label>
        <select class="fs" id="activity-category">
          <option value="Watch TV">Watch TV</option>
          <option value="Gaming">Gaming</option>
          <option value="Music">Music</option>
          <option value="Other">Other</option>
        </select>
      </div>
      <p style="color:var(--txt2);font-size:12px;">After creating, edit the activity to add actions.</p>
      <button class="btn btn-p" data-action="save-activity">Create Activity</button>
    `;
    this._render();
  }

  _addRoomModal() {
    this._modalContent=`<div class="modal-head"><h3>Add Room</h3><button class="modal-x" data-action="close-modal">&times;</button></div><div class="fg"><label class="fl">Name</label><input class="fi" id="room-name" placeholder="Living Room"></div><div class="fg"><label class="fl">Icon</label><input class="fi" id="room-icon" value="mdi:sofa"></div><button class="btn btn-p" data-action="save-room">Save</button>`;
    this._render();
  }

  _addDeviceModal() {
    this._editDeviceId=null;
    this._modalContent=`<div class="modal-head"><h3>Add Device</h3><button class="modal-x" data-action="close-modal">&times;</button></div><div class="fg"><label class="fl">Name</label><input class="fi" id="device-name" placeholder="Samsung TV"></div><div class="fr"><div class="fg"><label class="fl">Category</label><select class="fs" id="device-category"><option value="tv">TV</option><option value="projector">Projector</option><option value="receiver">Receiver</option><option value="soundbar">Soundbar</option><option value="streaming">Streaming</option><option value="cable_box">Cable Box</option><option value="ac">AC</option><option value="fan">Fan</option><option value="light">Light</option><option value="other">Other</option></select></div><div class="fg"><label class="fl">Room</label><select class="fs" id="device-room"><option value="">None</option>${this._data.rooms.map(r=>`<option value="${r.id}">${r.name}</option>`).join('')}</select></div></div><div class="fr"><div class="fg"><label class="fl">Brand</label><input class="fi" id="device-brand"></div><div class="fg"><label class="fl">Model</label><input class="fi" id="device-model"></div></div><button class="btn btn-p" data-action="save-device">Save</button>`;
    this._render();
  }

  _editDeviceModal(id) {
    const d=this._data.devices.find(x=>x.id===id); if(!d)return;
    this._editDeviceId=id;
    this._modalContent=`<div class="modal-head"><h3>Edit Device</h3><button class="modal-x" data-action="close-modal">&times;</button></div><div class="fg"><label class="fl">Name</label><input class="fi" id="device-name" value="${d.name}"></div><div class="fr"><div class="fg"><label class="fl">Category</label><select class="fs" id="device-category">${['tv','projector','receiver','soundbar','streaming','cable_box','ac','fan','light','other'].map(c=>`<option value="${c}" ${d.category===c?'selected':''}>${c}</option>`).join('')}</select></div><div class="fg"><label class="fl">Room</label><select class="fs" id="device-room"><option value="">None</option>${this._data.rooms.map(r=>`<option value="${r.id}" ${d.room_id===r.id?'selected':''}>${r.name}</option>`).join('')}</select></div></div><div class="fr"><div class="fg"><label class="fl">Brand</label><input class="fi" id="device-brand" value="${d.brand||''}"></div><div class="fg"><label class="fl">Model</label><input class="fi" id="device-model" value="${d.model||''}"></div></div><div class="fr"><div class="fg"><label class="fl">Power ON Cmd</label><select class="fs" id="device-power-on"><option value="">Auto</option>${Object.keys(d.commands||{}).map(c=>`<option value="${c}" ${d.power_on_command===c?'selected':''}>${c}</option>`).join('')}</select></div><div class="fg"><label class="fl">Power OFF Cmd</label><select class="fs" id="device-power-off"><option value="">Auto</option>${Object.keys(d.commands||{}).map(c=>`<option value="${c}" ${d.power_off_command===c?'selected':''}>${c}</option>`).join('')}</select></div></div><button class="btn btn-p" data-action="save-device">Save</button>`;
    this._render();
  }

  _addSceneModal() { this._selectedScene={name:'',icon:'mdi:play',actions:[]}; this._sceneModal(); }
  _editSceneModal(id) { this._selectedScene=JSON.parse(JSON.stringify(this._data.scenes.find(s=>s.id===id))); this._sceneModal(); }

  _sceneModal() {
    const s=this._selectedScene;
    this._modalContent=`<div class="modal-head"><h3>${s.id?'Edit':'Create'} Scene</h3><button class="modal-x" data-action="close-modal">&times;</button></div><div class="fr"><div class="fg"><label class="fl">Name</label><input class="fi" id="scene-name" value="${s.name||''}" placeholder="Watch Roku"></div><div class="fg"><label class="fl">Icon</label><input class="fi" id="scene-icon" value="${s.icon||'mdi:play'}"></div></div><div class="fg"><label class="fl">Actions</label><div class="tl" id="scene-actions">${(s.actions||[]).map((a,i)=>{const d=this._data.devices.find(x=>x.id===a.device_id);return`<div class="tl-item"><div class="tl-num">${i+1}</div><div class="tl-content"><select class="fs action-device" data-index="${i}">${this._data.devices.map(x=>`<option value="${x.id}" ${x.id===a.device_id?'selected':''}>${x.name}</option>`).join('')}</select><select class="fs action-command" data-index="${i}">${d?Object.keys(d.commands||{}).map(c=>`<option value="${c}" ${c===a.command_name?'selected':''}>${c}</option>`).join(''):''}</select></div><div class="tl-delay"><input class="fi" type="number" value="${a.delay_after||0.5}" step="0.1" data-index="${i}">s</div></div>`;}).join('')}</div><button class="btn btn-s btn-sm" id="add-action"><ha-icon icon="mdi:plus"></ha-icon>Add</button></div><button class="btn btn-p" data-action="save-scene">Save</button>`;
    this._render();
    this.shadowRoot.getElementById('add-action')?.addEventListener('click',()=>{
      this._selectedScene.actions.push({device_id:this._data.devices[0]?.id||'',command_name:'',delay_after:0.5});
      this._sceneModal();
    });
    this.shadowRoot.querySelectorAll('.action-device').forEach(sel=>sel.addEventListener('change',e=>{
      const d=this._data.devices.find(x=>x.id===e.target.value);
      const cmd=this.shadowRoot.querySelector(`.action-command[data-index="${e.target.dataset.index}"]`);
      if(cmd&&d)cmd.innerHTML=Object.keys(d.commands||{}).map(c=>`<option value="${c}">${c}</option>`).join('');
    }));
  }

  _learnModal(id) {
    this._learnDeviceId=id;
    const d=this._data.devices.find(x=>x.id===id);
    this._modalContent=`<div class="modal-head"><h3>Learn: ${d?.name||'Device'}</h3><button class="modal-x" data-action="close-modal">&times;</button></div><div class="fg"><label class="fl">Command Name</label><input class="fi" id="learn-command" placeholder="power"></div><p style="color:var(--txt2);font-size:12px;">Click Start, then press button within 15 seconds.</p><button class="btn btn-p" data-action="start-learn"><ha-icon icon="mdi:record"></ha-icon>Start</button>`;
    this._render();
  }

  async _saveRoom() {
    const n=this.shadowRoot.getElementById('room-name').value, i=this.shadowRoot.getElementById('room-icon').value;
    if(!n)return;
    await this._fetch('/api/omniremote/rooms',{method:'POST',body:JSON.stringify({name:n,icon:i})});
    this._modalContent=null; await this._loadData();
  }

  async _saveDevice() {
    const n=this.shadowRoot.getElementById('device-name').value; if(!n)return;
    const data={name:n, category:this.shadowRoot.getElementById('device-category').value, room_id:this.shadowRoot.getElementById('device-room').value||null, brand:this.shadowRoot.getElementById('device-brand')?.value||'', model:this.shadowRoot.getElementById('device-model')?.value||''};
    const pon=this.shadowRoot.getElementById('device-power-on'), poff=this.shadowRoot.getElementById('device-power-off');
    if(pon)data.power_on_command=pon.value||null;
    if(poff)data.power_off_command=poff.value||null;
    if(this._editDeviceId){data.id=this._editDeviceId;await this._fetch('/api/omniremote/devices',{method:'PUT',body:JSON.stringify(data)});this._editDeviceId=null;}
    else await this._fetch('/api/omniremote/devices',{method:'POST',body:JSON.stringify(data)});
    this._modalContent=null; await this._loadData();
  }

  async _saveScene() {
    const n=this.shadowRoot.getElementById('scene-name').value, i=this.shadowRoot.getElementById('scene-icon').value; if(!n)return;
    const actions=[];
    this.shadowRoot.querySelectorAll('.tl-item').forEach(item=>{
      actions.push({device_id:item.querySelector('.action-device').value, command_name:item.querySelector('.action-command').value, delay_after:parseFloat(item.querySelector('.tl-delay input').value)||0.5});
    });
    const data={name:n,icon:i,actions};
    if(this._selectedScene?.id)data.id=this._selectedScene.id;
    await this._fetch('/api/omniremote/scenes',{method:this._selectedScene?.id?'PUT':'POST',body:JSON.stringify(data)});
    this._modalContent=null; this._selectedScene=null; await this._loadData();
  }

  async _startLearn() {
    const cmd=this.shadowRoot.getElementById('learn-command').value; if(!cmd)return;
    this._learningCommand=cmd; this._isLearning=true; this._modalContent=null; this._render();
    try {
      const r=await this._fetch('/api/omniremote/learn',{method:'POST',body:JSON.stringify({device_id:this._learnDeviceId,command_name:cmd,timeout:15})});
      if(r.success)await this._loadData(); else alert('Failed: '+(r.error||'Timeout'));
    } catch(e){alert('Error: '+e.message);}
    this._isLearning=false; this._learningCommand=null; this._learnDeviceId=null; this._render();
  }

  async _sendCmd(id,cmd) { await this._fetch('/api/omniremote/commands',{method:'POST',body:JSON.stringify({action:'send',device_id:id,command_name:cmd})}); }

  async _togglePower(id) {
    const d=this._data.devices.find(x=>x.id===id); if(!d)return;
    const cmds=Object.keys(d.commands||{});
    let cmd=d.power_state?d.power_off_command:d.power_on_command;
    if(!cmd)cmd=d.power_state?cmds.find(c=>c.match(/off/i))||cmds.find(c=>c.match(/power/i)):cmds.find(c=>c.match(/^on$/i))||cmds.find(c=>c.match(/power/i));
    if(cmd){await this._sendCmd(id,cmd);await this._fetch('/api/omniremote/devices',{method:'PUT',body:JSON.stringify({id,power_state:!d.power_state})});await this._loadData();}
  }

  async _runScene(id) { await this._fetch('/api/omniremote/commands',{method:'POST',body:JSON.stringify({action:'run_scene',scene_id:id})}); }
}

customElements.define('omniremote-panel', OmniRemotePanel);
