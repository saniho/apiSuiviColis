import { LitElement, html, css, nothing } from "https://unpkg.com/lit-element@3/lit-element.js?module";

const STATUS_ORDER = [
  "exception", "delayed", "pending",
  "picked_up", "in_transit", "out_for_delivery",
  "available_for_pickup", "delivered",
];

const STATUS_COLORS = {
  delivered: "#43a047",
  out_for_delivery: "#1e88e5",
  in_transit: "#fb8c00",
  picked_up: "#8e24aa",
  exception: "#e53935",
  pending: "#757575",
  delayed: "#ff6f00",
  available_for_pickup: "#00897b",
};

const STATUS_ICONS = {
  delivered: "✓",
  out_for_delivery: "🚚",
  in_transit: "📦",
  picked_up: "📬",
  exception: "⚠",
  pending: "⏳",
  delayed: "⏰",
  available_for_pickup: "🏪",
};

const CARRIERS = [
  ["laposte", "La Poste"],
  ["colissimo", "Colissimo"],
  ["chronopost", "Chronopost"],
  ["dhl", "DHL"],
  ["fedex", "FedEx"],
  ["ups", "UPS"],
  ["tnt", "TNT"],
  ["gls", "GLS"],
  ["mondial_relay", "Mondial Relay"],
  ["amazon", "Amazon Logistics"],
  ["dpd", "DPD"],
  ["relais_colis", "Relais Colis"],
  ["other", "Autre transporteur"],
];

class MySuiviColisCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      viewMode: { type: String },
      packages: { type: Array },
      showModal: { type: Boolean },
      formData: { type: Object },
      formError: { type: String },
      submitting: { type: Boolean },
    };
  }

  constructor() {
    super();
    this.viewMode = "both";
    this.packages = [];
    this.showModal = false;
    this.formData = { name: "", tracking_number: "", carrier: "colissimo", postal_code: "" };
    this.formError = "";
    this.submitting = false;
    this._map = null;
    this._markers = [];
    this._leafletLoaded = false;
  }

  static get styles() {
    return css`
      :host {
        display: block;
        font-family: var(--paper-font-body1_-_font-family, "Roboto", sans-serif);
      }
      .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 16px;
        background: var(--card-background-color, white);
        border-bottom: 1px solid var(--divider-color, #e0e0e0);
        gap: 8px;
      }
      .card-title {
        font-size: 18px;
        font-weight: 500;
        color: var(--primary-text-color, #212121);
        display: flex;
        align-items: center;
        gap: 8px;
        flex-shrink: 0;
      }
      .header-actions {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        justify-content: flex-end;
      }
      .add-btn {
        border: none;
        background: var(--primary-color, #03a9f4);
        color: white;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        font-size: 20px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        transition: background 0.2s;
      }
      .add-btn:hover {
        filter: brightness(1.1);
      }
      .view-toggle {
        display: flex;
        gap: 4px;
        background: var(--secondary-background-color, #f5f5f5);
        border-radius: 8px;
        padding: 2px;
      }
      .view-btn {
        border: none;
        background: transparent;
        padding: 6px 10px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 12px;
        color: var(--secondary-text-color, #727272);
        transition: all 0.2s;
        white-space: nowrap;
      }
      .view-btn.active {
        background: var(--primary-color, #03a9f4);
        color: white;
      }
      .map-container {
        height: 300px;
        width: 100%;
        position: relative;
      }
      .map-container.hidden {
        display: none;
      }
      .list-container {
        padding: 0;
      }
      .list-container.hidden {
        display: none;
      }
      .package-item {
        display: flex;
        align-items: center;
        padding: 10px 16px;
        border-bottom: 1px solid var(--divider-color, #e0e0e0);
        cursor: pointer;
        transition: background 0.15s;
        position: relative;
      }
      .package-item:hover {
        background: var(--secondary-background-color, #f5f5f5);
      }
      .package-item:last-child {
        border-bottom: none;
      }
      .status-icon {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
        margin-right: 12px;
      }
      .package-info {
        flex: 1;
        min-width: 0;
      }
      .package-name {
        font-size: 14px;
        font-weight: 500;
        color: var(--primary-text-color, #212121);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .package-details {
        font-size: 12px;
        color: var(--secondary-text-color, #727272);
        margin-top: 2px;
      }
      .package-details.sub {
        font-size: 11px;
        opacity: 0.7;
        margin-top: 1px;
      }
      .tracking-num {
        font-weight: 500;
        color: var(--primary-text-color, #212121);
      }
      .package-status {
        font-size: 12px;
        font-weight: 500;
        text-align: right;
        flex-shrink: 0;
        margin-left: 8px;
      }
      .delete-btn {
        border: none;
        background: transparent;
        color: var(--secondary-text-color, #727272);
        width: 28px;
        height: 28px;
        border-radius: 50%;
        font-size: 16px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        opacity: 0;
        transition: all 0.2s;
        margin-left: 4px;
      }
      .package-item:hover .delete-btn {
        opacity: 1;
      }
      .delete-btn:hover {
        background: rgba(229, 57, 53, 0.1);
        color: #e53935;
      }
      .empty-state {
        padding: 24px;
        text-align: center;
        color: var(--secondary-text-color, #727272);
        font-size: 14px;
      }
      .footer {
        padding: 8px 16px;
        font-size: 11px;
        color: var(--secondary-text-color, #727272);
        text-align: right;
        border-top: 1px solid var(--divider-color, #e0e0e0);
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      /* Modal overlay */
      .modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        animation: fadeIn 0.2s;
      }
      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      .modal {
        background: var(--card-background-color, white);
        border-radius: 16px;
        padding: 24px;
        width: 90%;
        max-width: 420px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        animation: slideUp 0.25s;
      }
      @keyframes slideUp {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
      }
      .modal h2 {
        margin: 0 0 20px;
        font-size: 18px;
        font-weight: 500;
        color: var(--primary-text-color, #212121);
      }
      .form-field {
        margin-bottom: 16px;
      }
      .form-field label {
        display: block;
        font-size: 12px;
        font-weight: 500;
        color: var(--secondary-text-color, #727272);
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .form-field input,
      .form-field select {
        width: 100%;
        padding: 10px 12px;
        border: 1px solid var(--divider-color, #e0e0e0);
        border-radius: 8px;
        font-size: 14px;
        font-family: inherit;
        background: var(--input-background-color, white);
        color: var(--primary-text-color, #212121);
        box-sizing: border-box;
        outline: none;
        transition: border-color 0.2s;
      }
      .form-field input:focus,
      .form-field select:focus {
        border-color: var(--primary-color, #03a9f4);
      }
      .form-error {
        color: #e53935;
        font-size: 12px;
        margin-top: 4px;
      }
      .modal-actions {
        display: flex;
        gap: 8px;
        justify-content: flex-end;
        margin-top: 20px;
      }
      .modal-actions button {
        padding: 8px 20px;
        border-radius: 8px;
        font-size: 14px;
        font-family: inherit;
        cursor: pointer;
        border: none;
        transition: all 0.2s;
      }
      .btn-cancel {
        background: var(--secondary-background-color, #f5f5f5);
        color: var(--primary-text-color, #212121);
      }
      .btn-cancel:hover {
        filter: brightness(0.95);
      }
      .btn-submit {
        background: var(--primary-color, #03a9f4);
        color: white;
      }
      .btn-submit:hover {
        filter: brightness(1.1);
      }
      .btn-submit:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      /* confirmation dialog */
      .confirm-text {
        font-size: 14px;
        color: var(--primary-text-color, #212121);
        margin-bottom: 8px;
        line-height: 1.5;
      }
      .confirm-sub {
        font-size: 13px;
        color: var(--secondary-text-color, #727272);
        margin-bottom: 16px;
      }
      .btn-danger {
        background: #e53935;
        color: white;
      }
      .btn-danger:hover {
        filter: brightness(1.1);
      }
    `;
  }

  setConfig(config) {
    if (!config) return;
    this.config = {
      title: config.title || "My Suivi Colis",
      show_map: config.show_map !== false,
      show_list: config.show_list !== false,
      default_view: config.default_view || "both",
      entities: config.entities || [],
    };
    this.viewMode = this.config.default_view;
  }

  getCardSize() {
    return 4;
  }

  shouldUpdate(changedProps) {
    return changedProps.has("hass") || changedProps.has("packages") ||
      changedProps.has("viewMode") || changedProps.has("showModal") ||
      changedProps.has("formError") || changedProps.has("submitting");
  }

  willUpdate(changedProps) {
    if (changedProps.has("hass")) {
      this._updatePackages();
    }
  }

  updated(changedProps) {
    if (changedProps.has("packages") || changedProps.has("viewMode")) {
      if (this.viewMode === "map" || this.viewMode === "both") {
        this._initMap();
      }
    }
  }

  _updatePackages() {
    if (!this.hass || !this.hass.states) return;
    const entities = [];
    const stateKeys = Object.keys(this.hass.states);
    const domainEntities = stateKeys.filter(
      (key) => key.startsWith("sensor.") && key.includes("my_suivi_colis")
    );
    const configEntities = this.config.entities || [];
    const allEntities = [...new Set([...domainEntities, ...configEntities])];

    for (const entityId of allEntities) {
      const state = this.hass.states[entityId];
      if (!state) continue;
      const attrs = state.attributes || {};
      entities.push({
        entity_id: entityId,
        name: state.attributes.friendly_name || entityId,
        state: state.state,
        status: attrs.status || "pending",
        raw_status: attrs.raw_status,
        location: attrs.location,
        latitude: attrs.latitude,
        longitude: attrs.longitude,
        carrier: attrs.carrier,
        tracking_number: attrs.tracking_number,
        estimated_delivery: attrs.estimated_delivery,
        last_update: attrs.last_update,
        status_timestamp: attrs.timestamp,
        history: attrs.history || [],
      });
    }

    entities.sort((a, b) => {
      const aIdx = STATUS_ORDER.indexOf(a.status);
      const bIdx = STATUS_ORDER.indexOf(b.status);
      return (aIdx >= 0 ? aIdx : 99) - (bIdx >= 0 ? bIdx : 99);
    });

    this.packages = entities;
  }

  _loadLeaflet() {
    return new Promise((resolve) => {
      if (window.L) {
        this._leafletLoaded = true;
        resolve();
        return;
      }
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      document.head.appendChild(link);
      const script = document.createElement("script");
      script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
      script.onload = () => { this._leafletLoaded = true; resolve(); };
      document.body.appendChild(script);
    });
  }

  async _initMap() {
    await this._loadLeaflet();
    await this.updateComplete;
    const container = this.shadowRoot?.querySelector(".map-container-inner");
    if (!container) return;

    if (!this._map) {
      this._map = L.map(container, { zoomControl: true, attributionControl: true });
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 19,
      }).addTo(this._map);
    }
    this._updateMarkers();
    this._map.invalidateSize();
  }

  _updateMarkers() {
    if (!this._map) return;
    for (const m of this._markers) this._map.removeLayer(m);
    this._markers = [];

    const withCoords = this.packages.filter((p) => p.latitude != null && p.longitude != null);
    if (!withCoords.length) return;

    for (const pkg of withCoords) {
      const color = STATUS_COLORS[pkg.status] || "#757575";
      const marker = L.marker([pkg.latitude, pkg.longitude], {
        icon: L.divIcon({
          html: `<div style="width:32px;height:32px;border-radius:50%;background:${color};color:white;display:flex;align-items:center;justify-content:center;font-size:16px;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3);cursor:pointer;">${STATUS_ICONS[pkg.status] || "📦"}</div>`,
          className: "",
          iconSize: [32, 32],
          iconAnchor: [16, 16],
        }),
      }).addTo(this._map);

      marker.bindPopup(`
        <div style="font-family:Roboto,sans-serif;min-width:180px;">
          <div style="font-weight:500;font-size:14px;margin-bottom:4px;">${this._escapeHtml(pkg.name)}</div>
          <div style="font-size:12px;color:#666;margin-bottom:6px;">${this._escapeHtml(pkg.carrier || "")} · ${this._escapeHtml(pkg.tracking_number || "")}</div>
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${color};"></span>
            <span style="font-size:13px;font-weight:500;color:${color};">${this._escapeHtml(pkg.state || pkg.status)}</span>
          </div>
          <div style="font-size:12px;color:#666;">📍 ${pkg.location ? this._escapeHtml(pkg.location) : "Localisation inconnue"}</div>
          ${pkg.estimated_delivery ? `<div style="font-size:12px;color:#666;margin-top:2px;">📅 ${this._escapeHtml(pkg.estimated_delivery)}</div>` : ""}
        </div>
      `);
      this._markers.push(marker);
    }

    if (withCoords.length === 1) {
      this._map.setView([withCoords[0].latitude, withCoords[0].longitude], 8);
    } else {
      this._map.fitBounds(L.featureGroup(this._markers).getBounds().pad(0.2));
    }
  }

  _escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  _setViewMode(mode) {
    this.viewMode = mode;
  }

  _handlePackageClick(pkg) {
    if (pkg.latitude && pkg.longitude) {
      if (this.viewMode === "list") this.viewMode = "both";
      this._initMap();
      if (this._map) {
        this._map.setView([pkg.latitude, pkg.longitude], 12);
        setTimeout(() => this._map.invalidateSize(), 100);
      }
      const marker = this._markers.find((m, i) => {
        const p = this.packages.filter((p2) => p2.latitude && p2.longitude)[i];
        return p && p.entity_id === pkg.entity_id;
      });
      if (marker) marker.openPopup();
    }
  }

  /* ---- Modal management ---- */

  _openAddModal() {
    this.formData = { name: "", tracking_number: "", carrier: "colissimo", postal_code: "" };
    this.formError = "";
    this.showModal = true;
  }

  _closeModal() {
    this.showModal = false;
    this.formError = "";
    this.submitting = false;
  }

  _handleFormInput(e) {
    const field = e.target.dataset.field;
    this.formData = { ...this.formData, [field]: e.target.value };
  }

  async _handleAddSubmit() {
    const { name, tracking_number, carrier } = this.formData;
    if (!tracking_number.trim()) {
      this.formError = "Le numéro de suivi est requis.";
      return;
    }
    this.submitting = true;
    this.formError = "";
    try {
      const postal_code = (this.formData.postal_code || "").trim();
      await this.hass.callService("my_suivi_colis", "add_tracking", {
        name: name.trim(),
        tracking_number: tracking_number.trim(),
        carrier,
        postal_code,
      });
      this._closeModal();
    } catch (err) {
      this.formError = err.message || "Erreur lors de l'ajout.";
      this.submitting = false;
    }
  }

  _handleKeyDown(e) {
    if (e.key === "Enter") this._handleAddSubmit();
    if (e.key === "Escape") this._closeModal();
  }

  async _handleDelete(e, pkg) {
    e.stopPropagation();
    if (!confirm(`Supprimer le suivi de "${pkg.name}" ?`)) return;
    try {
      await this.hass.callService("my_suivi_colis", "remove_tracking", {
        tracking_number: pkg.tracking_number,
      });
    } catch (err) {
      alert(err.message || "Erreur lors de la suppression.");
    }
  }

  _formatDate(dateStr) {
    if (!dateStr) return "";
    try {
      return new Date(dateStr).toLocaleString("fr-FR", {
        day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
      });
    } catch { return dateStr; }
  }

  render() {
    if (!this.hass || !this.config) {
      return html`<ha-card><div class="empty-state">Configuration requise</div></ha-card>`;
    }

    const showMap = this.viewMode === "map" || this.viewMode === "both";
    const showList = this.viewMode === "list" || this.viewMode === "both";
    const count = this.packages.length;

    return html`
      <ha-card>
        <div class="card-header">
          <div class="card-title">📦 ${this.config.title}</div>
          <div class="header-actions">
            <button class="add-btn" title="Ajouter un colis" @click=${this._openAddModal}>+</button>
            <div class="view-toggle">
              <button class="view-btn ${this.viewMode === "list" ? "active" : ""}" @click=${() => this._setViewMode("list")}>📋 Liste</button>
              <button class="view-btn ${this.viewMode === "map" ? "active" : ""}" @click=${() => this._setViewMode("map")}>🗺️ Carte</button>
              <button class="view-btn ${this.viewMode === "both" ? "active" : ""}" @click=${() => this._setViewMode("both")}>Les deux</button>
            </div>
          </div>
        </div>

        <div class="map-container ${showMap ? "" : "hidden"}">
          <div class="map-container-inner" style="width:100%;height:100%;"></div>
        </div>

        <div class="list-container ${showList ? "" : "hidden"}">
          ${count === 0 ? html`
            <div class="empty-state">
              Aucun colis suivi.
              <br><br>
              <button class="view-btn" style="background:var(--primary-color,#03a9f4);color:white;padding:8px 16px;" @click=${this._openAddModal}>
                + Ajouter un colis
              </button>
            </div>
          ` : html`
            ${this.packages.map((pkg) => {
              const color = STATUS_COLORS[pkg.status] || "#757575";
              return html`
                <div class="package-item" @click=${() => this._handlePackageClick(pkg)}>
                  <div class="status-icon" style="background:${color};color:white;">
                    ${STATUS_ICONS[pkg.status] || "📦"}
                  </div>
                  <div class="package-info">
                    <div class="package-name">${pkg.name}</div>
                    <div class="package-details">
                      ${pkg.tracking_number ? html`<span class="tracking-num">#${pkg.tracking_number}</span>` : ""}
                      ${pkg.carrier ? html`<span>${pkg.carrier}</span>` : ""}
                      ${pkg.location ? html`<span> · ${pkg.location}</span>` : ""}
                      ${pkg.estimated_delivery ? html`<span> · ${pkg.estimated_delivery}</span>` : ""}
                    </div>
                    <div class="package-details sub">
                      ${pkg.raw_status ? html`<span>Statut brut : ${pkg.raw_status}</span>` : ""}
                      ${pkg.status_timestamp ? html`<span> · ${this._formatDate(pkg.status_timestamp)}</span>` : ""}
                    </div>
                  </div>
                  <div class="package-status" style="color:${color};">${pkg.state || pkg.status}</div>
                  <button class="delete-btn" title="Supprimer" @click=${(e) => this._handleDelete(e, pkg)}>✕</button>
                </div>
              `;
            })}
          `}
        </div>

        <div class="footer">
          <span>${count} colis</span>
          <span>${this._formatDate(new Date().toISOString())}</span>
        </div>
      </ha-card>

      ${this.showModal ? html`
        <div class="modal-overlay" @click=${this._closeModal} @keydown=${this._handleKeyDown} tabindex="0">
          <div class="modal" @click=${(e) => e.stopPropagation()}>
            <h2>Ajouter un colis</h2>

            <div class="form-field">
              <label>Nom (optionnel)</label>
              <input type="text" data-field="name" .value=${this.formData.name} @input=${this._handleFormInput} placeholder="Ex: Mon colis Amazon" />
            </div>

            <div class="form-field">
              <label>Numéro de suivi *</label>
              <input type="text" data-field="tracking_number" .value=${this.formData.tracking_number} @input=${this._handleFormInput} placeholder="Ex: 7A12345678900" />
            </div>

            <div class="form-field">
              <label>Transporteur *</label>
              <select data-field="carrier" .value=${this.formData.carrier} @change=${this._handleFormInput}>
                ${CARRIERS.map(([key, label]) => html`<option value=${key}>${label}</option>`)}
              </select>
            </div>

            <div class="form-field">
              <label>Code postal (optionnel)</label>
              <input type="text" data-field="postal_code" .value=${this.formData.postal_code} @input=${this._handleFormInput} placeholder="Ex: 75001 (utile pour Mondial Relay)" />
            </div>

            ${this.formError ? html`<div class="form-error">${this.formError}</div>` : ""}

            <div class="modal-actions">
              <button class="btn-cancel" @click=${this._closeModal} ?disabled=${this.submitting}>Annuler</button>
              <button class="btn-submit" @click=${this._handleAddSubmit} ?disabled=${this.submitting}>
                ${this.submitting ? "Ajout..." : "Ajouter"}
              </button>
            </div>
          </div>
        </div>
      ` : ""}
    `;
  }
}

customElements.define("my-suivi-colis-card", MySuiviColisCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "my-suivi-colis-card",
  name: "My Suivi Colis",
  description: "Suivi de colis avec carte et liste — Ajout/Suppression depuis la carte",
  preview: false,
});
