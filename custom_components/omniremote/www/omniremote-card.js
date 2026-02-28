/**
 * OmniRemote Card - Fully Customizable Remote Control Card
 * Supports custom layouts, themes, button mapping, and Bluetooth remote input
 */

const CARD_VERSION = '1.0.0';

// Default button templates for common device types
const REMOTE_TEMPLATES = {
  tv: {
    name: 'TV Remote',
    icon: 'mdi:television',
    layout: [
      ['power', null, 'input'],
      ['vol_up', 'mute', 'ch_up'],
      ['vol_down', null, 'ch_down'],
      [null, 'up', null],
      ['left', 'ok', 'right'],
      [null, 'down', null],
      ['back', 'home', 'menu'],
      ['num_1', 'num_2', 'num_3'],
      ['num_4', 'num_5', 'num_6'],
      ['num_7', 'num_8', 'num_9'],
      ['info', 'num_0', 'guide'],
    ],
    buttons: {
      power: { icon: 'mdi:power', color: '#e74c3c', command: 'power' },
      input: { icon: 'mdi:import', command: 'input' },
      vol_up: { icon: 'mdi:volume-plus', command: 'volume_up', repeat: true },
      vol_down: { icon: 'mdi:volume-minus', command: 'volume_down', repeat: true },
      mute: { icon: 'mdi:volume-off', command: 'mute' },
      ch_up: { icon: 'mdi:chevron-up', command: 'channel_up', repeat: true },
      ch_down: { icon: 'mdi:chevron-down', command: 'channel_down', repeat: true },
      up: { icon: 'mdi:chevron-up', command: 'up', repeat: true },
      down: { icon: 'mdi:chevron-down', command: 'down', repeat: true },
      left: { icon: 'mdi:chevron-left', command: 'left', repeat: true },
      right: { icon: 'mdi:chevron-right', command: 'right', repeat: true },
      ok: { icon: 'mdi:checkbox-blank-circle', command: 'ok', size: 'large' },
      back: { icon: 'mdi:arrow-left', command: 'back' },
      home: { icon: 'mdi:home', command: 'home' },
      menu: { icon: 'mdi:menu', command: 'menu' },
      info: { icon: 'mdi:information', command: 'info' },
      guide: { icon: 'mdi:television-guide', command: 'guide' },
      num_0: { label: '0', command: 'num_0' },
      num_1: { label: '1', command: 'num_1' },
      num_2: { label: '2', command: 'num_2' },
      num_3: { label: '3', command: 'num_3' },
      num_4: { label: '4', command: 'num_4' },
      num_5: { label: '5', command: 'num_5' },
      num_6: { label: '6', command: 'num_6' },
      num_7: { label: '7', command: 'num_7' },
      num_8: { label: '8', command: 'num_8' },
      num_9: { label: '9', command: 'num_9' },
    }
  },
  
  streaming: {
    name: 'Streaming Remote',
    icon: 'mdi:play-network',
    layout: [
      ['power', null, 'input'],
      [null, 'up', null],
      ['left', 'ok', 'right'],
      [null, 'down', null],
      ['back', 'home', 'menu'],
      ['rewind', 'play_pause', 'fast_forward'],
      ['vol_down', 'mute', 'vol_up'],
      ['netflix', 'youtube', 'prime'],
      ['disney', 'hulu', 'spotify'],
    ],
    buttons: {
      power: { icon: 'mdi:power', color: '#e74c3c', command: 'power' },
      input: { icon: 'mdi:import', command: 'input' },
      up: { icon: 'mdi:chevron-up', command: 'up', repeat: true },
      down: { icon: 'mdi:chevron-down', command: 'down', repeat: true },
      left: { icon: 'mdi:chevron-left', command: 'left', repeat: true },
      right: { icon: 'mdi:chevron-right', command: 'right', repeat: true },
      ok: { icon: 'mdi:checkbox-blank-circle', command: 'ok', size: 'large' },
      back: { icon: 'mdi:arrow-left', command: 'back' },
      home: { icon: 'mdi:home', command: 'home' },
      menu: { icon: 'mdi:menu', command: 'menu' },
      play_pause: { icon: 'mdi:play-pause', command: 'play_pause' },
      rewind: { icon: 'mdi:rewind', command: 'rewind', repeat: true },
      fast_forward: { icon: 'mdi:fast-forward', command: 'fast_forward', repeat: true },
      vol_up: { icon: 'mdi:volume-plus', command: 'volume_up', repeat: true },
      vol_down: { icon: 'mdi:volume-minus', command: 'volume_down', repeat: true },
      mute: { icon: 'mdi:volume-off', command: 'mute' },
      netflix: { icon: 'mdi:netflix', color: '#E50914', command: 'app_netflix', label: '' },
      youtube: { icon: 'mdi:youtube', color: '#FF0000', command: 'app_youtube', label: '' },
      prime: { icon: 'mdi:amazon', color: '#00A8E1', command: 'app_prime', label: '' },
      disney: { icon: 'mdi:movie-star', color: '#113CCF', command: 'app_disney', label: '' },
      hulu: { icon: 'mdi:hulu', color: '#1CE783', command: 'app_hulu', label: '' },
      spotify: { icon: 'mdi:spotify', color: '#1DB954', command: 'app_spotify', label: '' },
    }
  },
  
  receiver: {
    name: 'AV Receiver',
    icon: 'mdi:audio-video',
    layout: [
      ['power', 'mute', 'input'],
      ['vol_up', 'vol_display', 'vol_down'],
      ['hdmi_1', 'hdmi_2', 'hdmi_3'],
      ['hdmi_4', 'optical', 'bluetooth'],
      ['stereo', 'surround', 'dolby'],
      ['bass_up', 'treble_up', 'dialog_up'],
      ['bass_down', 'treble_down', 'dialog_down'],
    ],
    buttons: {
      power: { icon: 'mdi:power', color: '#e74c3c', command: 'power' },
      mute: { icon: 'mdi:volume-off', command: 'mute' },
      input: { icon: 'mdi:import', command: 'input' },
      vol_up: { icon: 'mdi:volume-plus', command: 'volume_up', repeat: true },
      vol_down: { icon: 'mdi:volume-minus', command: 'volume_down', repeat: true },
      vol_display: { label: 'VOL', command: null },
      hdmi_1: { label: 'HDMI 1', command: 'hdmi_1' },
      hdmi_2: { label: 'HDMI 2', command: 'hdmi_2' },
      hdmi_3: { label: 'HDMI 3', command: 'hdmi_3' },
      hdmi_4: { label: 'HDMI 4', command: 'hdmi_4' },
      optical: { label: 'OPT', command: 'optical' },
      bluetooth: { icon: 'mdi:bluetooth', command: 'bluetooth' },
      stereo: { label: 'STEREO', command: 'mode_stereo' },
      surround: { label: 'SURR', command: 'mode_surround' },
      dolby: { label: 'DOLBY', command: 'mode_dolby' },
      bass_up: { label: 'BASS+', command: 'bass_up' },
      bass_down: { label: 'BASS-', command: 'bass_down' },
      treble_up: { label: 'TREB+', command: 'treble_up' },
      treble_down: { label: 'TREB-', command: 'treble_down' },
      dialog_up: { label: 'DIAL+', command: 'dialog_up' },
      dialog_down: { label: 'DIAL-', command: 'dialog_down' },
    }
  },
  
  projector: {
    name: 'Projector',
    icon: 'mdi:projector',
    layout: [
      ['power_on', null, 'power_off'],
      ['input', 'blank', 'freeze'],
      ['hdmi_1', 'hdmi_2', 'vga'],
      ['zoom_in', 'focus', 'zoom_out'],
      ['keystone_up', null, 'keystone_down'],
      ['menu', 'ok', 'back'],
      ['up', null, null],
      ['left', 'down', 'right'],
      ['eco', 'picture', 'aspect'],
    ],
    buttons: {
      power_on: { icon: 'mdi:power', color: '#27ae60', command: 'power_on', label: 'ON' },
      power_off: { icon: 'mdi:power', color: '#e74c3c', command: 'power_off', label: 'OFF' },
      input: { icon: 'mdi:import', command: 'input' },
      blank: { icon: 'mdi:projector-screen', command: 'blank' },
      freeze: { icon: 'mdi:snowflake', command: 'freeze' },
      hdmi_1: { label: 'HDMI 1', command: 'hdmi_1' },
      hdmi_2: { label: 'HDMI 2', command: 'hdmi_2' },
      vga: { label: 'VGA', command: 'vga' },
      zoom_in: { icon: 'mdi:magnify-plus', command: 'zoom_in' },
      zoom_out: { icon: 'mdi:magnify-minus', command: 'zoom_out' },
      focus: { icon: 'mdi:focus-field', command: 'focus' },
      keystone_up: { icon: 'mdi:arrow-collapse-up', command: 'keystone_up' },
      keystone_down: { icon: 'mdi:arrow-collapse-down', command: 'keystone_down' },
      menu: { icon: 'mdi:menu', command: 'menu' },
      ok: { icon: 'mdi:check', command: 'ok' },
      back: { icon: 'mdi:arrow-left', command: 'back' },
      up: { icon: 'mdi:chevron-up', command: 'up' },
      down: { icon: 'mdi:chevron-down', command: 'down' },
      left: { icon: 'mdi:chevron-left', command: 'left' },
      right: { icon: 'mdi:chevron-right', command: 'right' },
      eco: { icon: 'mdi:leaf', command: 'eco_mode' },
      picture: { icon: 'mdi:image', command: 'picture_mode' },
      aspect: { icon: 'mdi:aspect-ratio', command: 'aspect_ratio' },
    }
  },
  
  fan: {
    name: 'Fan/AC',
    icon: 'mdi:fan',
    layout: [
      ['power', null, 'timer'],
      ['speed_1', 'speed_2', 'speed_3'],
      ['temp_up', 'display', 'temp_down'],
      ['mode', 'swing', 'sleep'],
      ['light', 'natural', 'turbo'],
    ],
    buttons: {
      power: { icon: 'mdi:power', color: '#e74c3c', command: 'power' },
      timer: { icon: 'mdi:timer', command: 'timer' },
      speed_1: { label: '1', command: 'speed_1' },
      speed_2: { label: '2', command: 'speed_2' },
      speed_3: { label: '3', command: 'speed_3' },
      temp_up: { icon: 'mdi:thermometer-plus', command: 'temp_up', repeat: true },
      temp_down: { icon: 'mdi:thermometer-minus', command: 'temp_down', repeat: true },
      display: { icon: 'mdi:thermometer', command: null },
      mode: { icon: 'mdi:air-conditioner', command: 'mode' },
      swing: { icon: 'mdi:swap-vertical', command: 'swing' },
      sleep: { icon: 'mdi:sleep', command: 'sleep' },
      light: { icon: 'mdi:lightbulb', command: 'light' },
      natural: { icon: 'mdi:weather-windy', command: 'natural' },
      turbo: { icon: 'mdi:fan-speed-3', command: 'turbo' },
    }
  },
  
  minimal: {
    name: 'Minimal',
    icon: 'mdi:remote',
    layout: [
      ['power'],
      ['up'],
      ['left', 'ok', 'right'],
      ['down'],
      ['back', 'home'],
    ],
    buttons: {
      power: { icon: 'mdi:power', color: '#e74c3c', command: 'power' },
      up: { icon: 'mdi:chevron-up', command: 'up', repeat: true },
      down: { icon: 'mdi:chevron-down', command: 'down', repeat: true },
      left: { icon: 'mdi:chevron-left', command: 'left', repeat: true },
      right: { icon: 'mdi:chevron-right', command: 'right', repeat: true },
      ok: { icon: 'mdi:checkbox-blank-circle', command: 'ok', size: 'large' },
      back: { icon: 'mdi:arrow-left', command: 'back' },
      home: { icon: 'mdi:home', command: 'home' },
    }
  },
  
  custom: {
    name: 'Custom',
    icon: 'mdi:puzzle',
    layout: [],
    buttons: {}
  }
};

// Color themes
const THEMES = {
  default: {
    name: 'Default',
    background: 'var(--card-background-color)',
    buttonBg: 'var(--primary-background-color)',
    buttonText: 'var(--primary-text-color)',
    buttonActive: 'var(--primary-color)',
    accent: 'var(--primary-color)',
  },
  dark: {
    name: 'Dark',
    background: '#1a1a2e',
    buttonBg: '#16213e',
    buttonText: '#eaeaea',
    buttonActive: '#0f3460',
    accent: '#e94560',
  },
  glass: {
    name: 'Glass',
    background: 'rgba(255,255,255,0.1)',
    buttonBg: 'rgba(255,255,255,0.15)',
    buttonText: '#ffffff',
    buttonActive: 'rgba(255,255,255,0.3)',
    accent: '#00d4ff',
  },
  retro: {
    name: 'Retro',
    background: '#2d2d2d',
    buttonBg: '#4a4a4a',
    buttonText: '#f5f5dc',
    buttonActive: '#8b4513',
    accent: '#cd853f',
  },
  neon: {
    name: 'Neon',
    background: '#0a0a0a',
    buttonBg: '#1a1a1a',
    buttonText: '#00ff88',
    buttonActive: '#003322',
    accent: '#00ff88',
  },
};


class OmniRemoteCard extends HTMLElement {
  static get properties() {
    return {
      hass: {},
      config: {},
    };
  }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._config = null;
    this._pressTimer = null;
    this._repeatInterval = null;
    this._editMode = false;
    this._draggedButton = null;
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    // Support profile-based configuration
    if (!config.device && !config.entity && !config.profile) {
      throw new Error('You need to define a device, entity, or profile');
    }
    
    this._config = {
      profile: config.profile || null, // Remote Builder profile ID
      device: config.device || null,
      entity: config.entity || null,
      room: config.room || null,
      blaster: config.blaster || null,
      area: config.area || null,
      template: config.template || 'tv',
      name: config.name || config.device || 'Remote',
      theme: config.theme || 'default',
      size: config.size || 'medium',
      columns: config.columns || null,
      show_name: config.show_name !== false,
      show_header: config.show_header !== false,
      show_room: config.show_room !== false,
      show_device_state: config.show_device_state !== false,
      custom_layout: config.custom_layout || null,
      custom_buttons: config.custom_buttons || {},
      button_size: config.button_size || 48,
      button_gap: config.button_gap || 8,
      border_radius: config.border_radius || 12,
      haptic: config.haptic !== false,
      double_tap_threshold: config.double_tap_threshold || 300,
      hold_threshold: config.hold_threshold || 500,
      repeat_delay: config.repeat_delay || 150,
      bluetooth_remote: config.bluetooth_remote || null,
    };
    
    // If profile is specified, load it from API
    if (this._config.profile) {
      this._loadProfile(this._config.profile);
    } else {
      this._render();
    }
  }
  
  async _loadProfile(profileId) {
    try {
      const response = await fetch('/api/omniremote/remote_profiles');
      const data = await response.json();
      const profile = data.profiles?.find(p => p.id === profileId);
      
      if (profile) {
        this._profile = profile;
        this._config.name = profile.name || this._config.name;
        this._config.custom_layout = this._buildLayoutFromProfile(profile);
        this._config.custom_buttons = this._buildButtonsFromProfile(profile);
        if (profile.room_id) this._config.room = profile.room_id;
        if (profile.blaster_id) this._config.blaster = profile.blaster_id;
        if (profile.default_device_id) this._config.device = profile.default_device_id;
      }
    } catch (err) {
      console.error('[OmniRemote Card] Error loading profile:', err);
    }
    
    this._render();
  }
  
  _buildLayoutFromProfile(profile) {
    if (!profile.buttons || !profile.rows || !profile.cols) return null;
    
    const layout = [];
    for (let r = 0; r < profile.rows; r++) {
      const row = [];
      for (let c = 0; c < profile.cols; c++) {
        const btn = profile.buttons.find(b => b.row === r && b.col === c);
        row.push(btn ? btn.id : null);
      }
      layout.push(row);
    }
    return layout;
  }
  
  _buildButtonsFromProfile(profile) {
    if (!profile.buttons) return {};
    
    const buttons = {};
    profile.buttons.forEach(btn => {
      buttons[btn.id] = {
        icon: btn.icon || 'mdi:circle',
        label: btn.label || '',
        color: btn.color || null,
        command: btn.command_name || null,
        device: btn.device_id || null,
        scene: btn.scene_id || null,
        action_type: btn.action_type || 'ir_command',
        col_span: btn.col_span || 1,
        row_span: btn.row_span || 1,
      };
    });
    return buttons;
  }

  getCardSize() {
    const template = REMOTE_TEMPLATES[this._config?.template] || REMOTE_TEMPLATES.tv;
    const layout = this._config?.custom_layout || template.layout;
    return Math.ceil(layout.length * 0.8) + 1;
  }

  static getConfigElement() {
    return document.createElement('omniremote-card-editor');
  }

  static getStubConfig() {
    return {
      device: '',
      template: 'tv',
      theme: 'default',
    };
  }

  _render() {
    if (!this._config || !this._hass) return;

    const template = REMOTE_TEMPLATES[this._config.template] || REMOTE_TEMPLATES.tv;
    const theme = THEMES[this._config.theme] || THEMES.default;
    const layout = this._config.custom_layout || template.layout;
    const buttons = { ...template.buttons, ...this._config.custom_buttons };
    const columns = this._config.columns || Math.max(...layout.map(row => row.length));

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --remote-bg: ${theme.background};
          --button-bg: ${theme.buttonBg};
          --button-text: ${theme.buttonText};
          --button-active: ${theme.buttonActive};
          --accent-color: ${theme.accent};
          --button-size: ${this._config.button_size}px;
          --button-gap: ${this._config.button_gap}px;
          --border-radius: ${this._config.border_radius}px;
        }
        
        ha-card {
          background: var(--remote-bg);
          border-radius: var(--border-radius);
          padding: 16px;
          overflow: hidden;
        }
        
        .remote-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .remote-title {
          display: flex;
          align-items: center;
          gap: 8px;
          color: var(--button-text);
          font-size: 1.1em;
          font-weight: 500;
        }
        
        .remote-title ha-icon {
          color: var(--accent-color);
        }
        
        .device-state {
          font-size: 0.85em;
          color: var(--accent-color);
          opacity: 0.8;
        }
        
        .remote-actions {
          display: flex;
          gap: 8px;
        }
        
        .action-btn {
          background: none;
          border: none;
          color: var(--button-text);
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
          opacity: 0.6;
          transition: opacity 0.2s;
        }
        
        .action-btn:hover {
          opacity: 1;
        }
        
        .remote-grid {
          display: flex;
          flex-direction: column;
          gap: var(--button-gap);
          align-items: center;
        }
        
        .remote-row {
          display: flex;
          gap: var(--button-gap);
          justify-content: center;
        }
        
        .remote-button {
          width: var(--button-size);
          height: var(--button-size);
          border: none;
          border-radius: calc(var(--border-radius) / 2);
          background: var(--button-bg);
          color: var(--button-text);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.15s ease;
          user-select: none;
          -webkit-tap-highlight-color: transparent;
          position: relative;
          overflow: hidden;
          font-size: 0.75em;
          font-weight: 500;
        }
        
        .remote-button:hover {
          transform: scale(1.05);
          box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        
        .remote-button:active, .remote-button.active {
          transform: scale(0.95);
          background: var(--button-active);
        }
        
        .remote-button.large {
          width: calc(var(--button-size) * 1.3);
          height: calc(var(--button-size) * 1.3);
        }
        
        .remote-button.wide {
          width: calc(var(--button-size) * 2 + var(--button-gap));
        }
        
        .remote-button.tall {
          height: calc(var(--button-size) * 2 + var(--button-gap));
        }
        
        .remote-button.empty {
          background: transparent;
          cursor: default;
          pointer-events: none;
        }
        
        .remote-button.color-btn {
          color: #fff;
        }
        
        .remote-button ha-icon {
          --mdc-icon-size: calc(var(--button-size) * 0.5);
        }
        
        .remote-button .btn-label {
          font-size: 0.85em;
          font-weight: 600;
        }
        
        .remote-button .ripple {
          position: absolute;
          border-radius: 50%;
          background: rgba(255,255,255,0.4);
          transform: scale(0);
          animation: ripple 0.6s linear;
          pointer-events: none;
        }
        
        @keyframes ripple {
          to {
            transform: scale(4);
            opacity: 0;
          }
        }
        
        /* Edit mode styles */
        .edit-mode .remote-button {
          cursor: move;
        }
        
        .edit-mode .remote-button.drag-over {
          border: 2px dashed var(--accent-color);
        }
        
        .edit-mode .remote-button::after {
          content: '';
          position: absolute;
          top: 2px;
          right: 2px;
          width: 8px;
          height: 8px;
          background: var(--accent-color);
          border-radius: 50%;
        }
        
        /* Bluetooth indicator */
        .bt-indicator {
          position: absolute;
          top: 8px;
          right: 8px;
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 0.7em;
          color: var(--accent-color);
          opacity: 0.8;
        }
        
        .bt-indicator.connected {
          color: #27ae60;
        }
        
        .bt-indicator ha-icon {
          --mdc-icon-size: 14px;
        }
        
        /* Area badge */
        .area-badge {
          background: var(--accent-color);
          color: #fff;
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 0.7em;
          margin-left: 8px;
        }
        
        /* Activity indicators */
        .activity-row {
          display: flex;
          gap: 8px;
          margin-top: 12px;
          padding-top: 12px;
          border-top: 1px solid rgba(255,255,255,0.1);
          flex-wrap: wrap;
          justify-content: center;
        }
        
        .activity-btn {
          background: var(--button-bg);
          border: 1px solid var(--accent-color);
          color: var(--accent-color);
          padding: 6px 12px;
          border-radius: 16px;
          font-size: 0.75em;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .activity-btn:hover {
          background: var(--accent-color);
          color: #fff;
        }
      </style>
      
      <ha-card>
        ${this._config.show_name ? `
          <div class="remote-header">
            <div class="remote-title">
              <ha-icon icon="${template.icon}"></ha-icon>
              <span>${this._config.name}</span>
              ${this._config.area ? `<span class="area-badge">${this._config.area}</span>` : ''}
            </div>
            ${this._config.show_device_state ? `
              <span class="device-state">${this._getDeviceState()}</span>
            ` : ''}
            <div class="remote-actions">
              <button class="action-btn" title="Edit Layout" @click="${() => this._toggleEditMode()}">
                <ha-icon icon="mdi:pencil"></ha-icon>
              </button>
            </div>
          </div>
        ` : ''}
        
        ${this._config.bluetooth_remote ? `
          <div class="bt-indicator ${this._isBluetoothConnected() ? 'connected' : ''}">
            <ha-icon icon="mdi:bluetooth"></ha-icon>
            <span>${this._isBluetoothConnected() ? 'Connected' : 'Disconnected'}</span>
          </div>
        ` : ''}
        
        <div class="remote-grid ${this._editMode ? 'edit-mode' : ''}">
          ${layout.map((row, rowIndex) => `
            <div class="remote-row" data-row="${rowIndex}">
              ${row.map((btnId, colIndex) => {
                if (btnId === null) {
                  return `<div class="remote-button empty"></div>`;
                }
                const btn = buttons[btnId] || { label: btnId, command: btnId };
                const colorStyle = btn.color ? `background-color: ${btn.color};` : '';
                const sizeClass = btn.size || '';
                return `
                  <button 
                    class="remote-button ${sizeClass} ${btn.color ? 'color-btn' : ''}"
                    data-button="${btnId}"
                    data-command="${btn.command || ''}"
                    data-repeat="${btn.repeat || false}"
                    style="${colorStyle}"
                    draggable="${this._editMode}"
                  >
                    ${btn.icon ? `<ha-icon icon="${btn.icon}"></ha-icon>` : ''}
                    ${btn.label !== undefined ? `<span class="btn-label">${btn.label}</span>` : ''}
                  </button>
                `;
              }).join('')}
            </div>
          `).join('')}
        </div>
        
        ${this._config.activities ? `
          <div class="activity-row">
            ${this._config.activities.map(act => `
              <button class="activity-btn" data-activity="${act.id}">
                ${act.icon ? `<ha-icon icon="${act.icon}"></ha-icon>` : ''}
                ${act.name}
              </button>
            `).join('')}
          </div>
        ` : ''}
      </ha-card>
    `;

    this._attachEventListeners();
  }

  _attachEventListeners() {
    // Button press handlers
    this.shadowRoot.querySelectorAll('.remote-button:not(.empty)').forEach(btn => {
      const command = btn.dataset.command;
      const canRepeat = btn.dataset.repeat === 'true';
      
      // Touch/mouse start
      const startHandler = (e) => {
        e.preventDefault();
        this._createRipple(btn, e);
        btn.classList.add('active');
        
        if (this._config.haptic && navigator.vibrate) {
          navigator.vibrate(10);
        }
        
        // Start hold timer
        this._pressTimer = setTimeout(() => {
          if (canRepeat) {
            this._repeatInterval = setInterval(() => {
              this._sendCommand(command);
            }, this._config.repeat_delay);
          }
        }, this._config.hold_threshold);
        
        this._sendCommand(command);
      };
      
      // Touch/mouse end
      const endHandler = () => {
        btn.classList.remove('active');
        clearTimeout(this._pressTimer);
        clearInterval(this._repeatInterval);
      };
      
      btn.addEventListener('mousedown', startHandler);
      btn.addEventListener('touchstart', startHandler, { passive: false });
      btn.addEventListener('mouseup', endHandler);
      btn.addEventListener('mouseleave', endHandler);
      btn.addEventListener('touchend', endHandler);
      btn.addEventListener('touchcancel', endHandler);
    });
    
    // Activity buttons
    this.shadowRoot.querySelectorAll('.activity-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this._runActivity(btn.dataset.activity);
      });
    });
    
    // Edit mode drag and drop
    if (this._editMode) {
      this._setupDragAndDrop();
    }
  }

  _createRipple(button, event) {
    const ripple = document.createElement('span');
    ripple.classList.add('ripple');
    
    const rect = button.getBoundingClientRect();
    const x = (event.clientX || event.touches?.[0]?.clientX || rect.left + rect.width / 2) - rect.left;
    const y = (event.clientY || event.touches?.[0]?.clientY || rect.top + rect.height / 2) - rect.top;
    
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    
    button.appendChild(ripple);
    
    setTimeout(() => ripple.remove(), 600);
  }

  _sendCommand(command) {
    if (!command || !this._hass) return;
    
    const device = this._config.device;
    const entity = this._config.entity;
    
    if (device) {
      // Use OmniRemote service
      this._hass.callService('omniremote', 'send_code', {
        device: device,
        command: command,
      });
    } else if (entity) {
      // Use remote entity
      this._hass.callService('remote', 'send_command', {
        entity_id: entity,
        command: command,
      });
    }
  }

  _runActivity(activityId) {
    if (!this._hass) return;
    
    this._hass.callService('omniremote', 'run_activity', {
      activity: activityId,
    });
  }

  _getDeviceState() {
    if (!this._hass || !this._config.entity) return '';
    
    const entity = this._hass.states[this._config.entity];
    if (!entity) return '';
    
    return entity.state === 'on' ? 'On' : 'Off';
  }

  _isBluetoothConnected() {
    if (!this._hass || !this._config.bluetooth_remote) return false;
    
    const btEntity = this._hass.states[`sensor.omniremote_bt_${this._config.bluetooth_remote}`];
    return btEntity?.state === 'connected';
  }

  _toggleEditMode() {
    this._editMode = !this._editMode;
    this._render();
  }

  _setupDragAndDrop() {
    const buttons = this.shadowRoot.querySelectorAll('.remote-button:not(.empty)');
    
    buttons.forEach(btn => {
      btn.addEventListener('dragstart', (e) => {
        this._draggedButton = btn.dataset.button;
        e.dataTransfer.effectAllowed = 'move';
      });
      
      btn.addEventListener('dragover', (e) => {
        e.preventDefault();
        btn.classList.add('drag-over');
      });
      
      btn.addEventListener('dragleave', () => {
        btn.classList.remove('drag-over');
      });
      
      btn.addEventListener('drop', (e) => {
        e.preventDefault();
        btn.classList.remove('drag-over');
        
        if (this._draggedButton && this._draggedButton !== btn.dataset.button) {
          this._swapButtons(this._draggedButton, btn.dataset.button);
        }
        this._draggedButton = null;
      });
    });
  }

  _swapButtons(btn1Id, btn2Id) {
    // Fire event to parent to update config
    this.dispatchEvent(new CustomEvent('config-changed', {
      detail: {
        config: {
          ...this._config,
          // Swap logic would go here
        }
      },
      bubbles: true,
      composed: true,
    }));
  }
}


/**
 * Card Editor for visual configuration
 */
class OmniRemoteCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  setConfig(config) {
    this._config = config;
    this._render();
  }

  _render() {
    if (!this._hass) return;

    // Get available devices from OmniRemote
    const devices = this._getOmniRemoteDevices();
    const areas = this._getAreas();
    const btRemotes = this._getBluetoothRemotes();

    this.shadowRoot.innerHTML = `
      <style>
        .editor {
          padding: 16px;
        }
        
        .field {
          margin-bottom: 16px;
        }
        
        .field label {
          display: block;
          margin-bottom: 4px;
          font-weight: 500;
        }
        
        .field select, .field input {
          width: 100%;
          padding: 8px;
          border: 1px solid var(--divider-color);
          border-radius: 4px;
          background: var(--card-background-color);
          color: var(--primary-text-color);
        }
        
        .field-row {
          display: flex;
          gap: 16px;
        }
        
        .field-row .field {
          flex: 1;
        }
        
        .section-title {
          font-size: 1.1em;
          font-weight: 600;
          margin: 24px 0 12px;
          padding-bottom: 8px;
          border-bottom: 1px solid var(--divider-color);
        }
        
        .template-preview {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 8px;
          margin-top: 8px;
        }
        
        .template-option {
          padding: 12px;
          border: 2px solid var(--divider-color);
          border-radius: 8px;
          cursor: pointer;
          text-align: center;
          transition: all 0.2s;
        }
        
        .template-option:hover {
          border-color: var(--primary-color);
        }
        
        .template-option.selected {
          border-color: var(--primary-color);
          background: var(--primary-color);
          color: #fff;
        }
        
        .template-option ha-icon {
          display: block;
          margin: 0 auto 4px;
        }
        
        .checkbox-field {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .checkbox-field input {
          width: auto;
        }
      </style>
      
      <div class="editor">
        <div class="field">
          <label>Device</label>
          <select id="device" @change="${(e) => this._valueChanged('device', e.target.value)}">
            <option value="">Select a device...</option>
            ${devices.map(d => `
              <option value="${d.name}" ${this._config.device === d.name ? 'selected' : ''}>
                ${d.name}
              </option>
            `).join('')}
          </select>
        </div>
        
        <div class="field">
          <label>Area/Room</label>
          <select id="area" @change="${(e) => this._valueChanged('area', e.target.value)}">
            <option value="">No specific area</option>
            ${areas.map(a => `
              <option value="${a.name}" ${this._config.area === a.name ? 'selected' : ''}>
                ${a.name}
              </option>
            `).join('')}
          </select>
        </div>
        
        <div class="section-title">Remote Template</div>
        <div class="template-preview">
          ${Object.entries(REMOTE_TEMPLATES).map(([id, tmpl]) => `
            <div 
              class="template-option ${this._config.template === id ? 'selected' : ''}"
              data-template="${id}"
            >
              <ha-icon icon="${tmpl.icon}"></ha-icon>
              <span>${tmpl.name}</span>
            </div>
          `).join('')}
        </div>
        
        <div class="section-title">Appearance</div>
        <div class="field-row">
          <div class="field">
            <label>Theme</label>
            <select id="theme" @change="${(e) => this._valueChanged('theme', e.target.value)}">
              ${Object.entries(THEMES).map(([id, t]) => `
                <option value="${id}" ${this._config.theme === id ? 'selected' : ''}>
                  ${t.name}
                </option>
              `).join('')}
            </select>
          </div>
          <div class="field">
            <label>Button Size</label>
            <input 
              type="number" 
              id="button_size" 
              min="32" 
              max="80" 
              value="${this._config.button_size || 48}"
              @change="${(e) => this._valueChanged('button_size', parseInt(e.target.value))}"
            />
          </div>
        </div>
        
        <div class="field-row">
          <div class="field checkbox-field">
            <input 
              type="checkbox" 
              id="show_name" 
              ${this._config.show_name !== false ? 'checked' : ''}
              @change="${(e) => this._valueChanged('show_name', e.target.checked)}"
            />
            <label for="show_name">Show Name</label>
          </div>
          <div class="field checkbox-field">
            <input 
              type="checkbox" 
              id="haptic" 
              ${this._config.haptic !== false ? 'checked' : ''}
              @change="${(e) => this._valueChanged('haptic', e.target.checked)}"
            />
            <label for="haptic">Haptic Feedback</label>
          </div>
        </div>
        
        <div class="section-title">Bluetooth Remote</div>
        <div class="field">
          <label>Linked Bluetooth Remote</label>
          <select id="bluetooth_remote" @change="${(e) => this._valueChanged('bluetooth_remote', e.target.value)}">
            <option value="">None</option>
            ${btRemotes.map(r => `
              <option value="${r.id}" ${this._config.bluetooth_remote === r.id ? 'selected' : ''}>
                ${r.name}
              </option>
            `).join('')}
          </select>
        </div>
        
        <div class="field">
          <label>Custom Name</label>
          <input 
            type="text" 
            id="name" 
            value="${this._config.name || ''}"
            placeholder="Override device name"
            @change="${(e) => this._valueChanged('name', e.target.value)}"
          />
        </div>
      </div>
    `;

    // Attach event listeners
    this.shadowRoot.querySelectorAll('.template-option').forEach(opt => {
      opt.addEventListener('click', () => {
        this._valueChanged('template', opt.dataset.template);
      });
    });
    
    this.shadowRoot.querySelectorAll('select, input').forEach(el => {
      el.addEventListener('change', (e) => {
        const field = e.target.id;
        let value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
        if (e.target.type === 'number') value = parseInt(value);
        this._valueChanged(field, value);
      });
    });
  }

  _valueChanged(field, value) {
    if (this._config[field] === value) return;
    
    const newConfig = { ...this._config, [field]: value };
    
    this.dispatchEvent(new CustomEvent('config-changed', {
      detail: { config: newConfig },
      bubbles: true,
      composed: true,
    }));
  }

  _getOmniRemoteDevices() {
    // This would fetch from the OmniRemote integration
    // For now return empty array - will be populated by integration
    return [];
  }

  _getAreas() {
    if (!this._hass) return [];
    return Object.values(this._hass.areas || {});
  }

  _getBluetoothRemotes() {
    // This would fetch registered BT remotes from OmniRemote
    return [];
  }
}


// Register the cards
customElements.define('omniremote-card', OmniRemoteCard);
customElements.define('omniremote-card-editor', OmniRemoteCardEditor);

// Register with HACS/Lovelace
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'omniremote-card',
  name: 'OmniRemote Card',
  description: 'Fully customizable remote control card with Bluetooth remote support',
  preview: true,
  documentationURL: 'https://github.com/HunterAviator/omniremote',
});

console.info(
  `%c OMNIREMOTE-CARD %c v${CARD_VERSION} `,
  'color: white; background: #e74c3c; font-weight: bold;',
  'color: #e74c3c; background: white; font-weight: bold;'
);
