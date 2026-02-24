/**
 * OmniRemote Manager Panel v1.2.3
 * Uses event delegation for reliable button handling in Shadow DOM
 */

const OMNIREMOTE_VERSION = "1.2.3";

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
    const opts = { 
      method, 
      headers: { 'Content-Type': 'application/json' }, 
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
      
      // Handle empty response
      if (!text || text.trim() === '') {
        console.log('[OmniRemote] Empty response');
        return {};
      }
      
      // Try to parse as JSON
      try {
        const json = JSON.parse(text);
        console.log(`[OmniRemote] API response:`, json);
        return json;
      } catch (parseError) {
        console.error(`[OmniRemote] JSON parse error:`, parseError, 'Response:', text.substring(0, 500));
        return { error: `Invalid JSON: ${text.substring(0, 200)}` };
      }
    } catch (e) {
      console.error(`[OmniRemote] API fetch error:`, e);
      return { error: e.message };
    }
  }