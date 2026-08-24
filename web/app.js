const state = { photos: [], filtered: [], visible: [], markers: [], map: null, currentPhotoId: null };
const $ = (id) => document.getElementById(id);

function formatDate(value) { return value ? new Date(value.replace(' ', 'T')).toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Date unknown'; }
function countries(photos) { return [...new Set(photos.map(photo => photo.country).filter(Boolean))].sort(); }
function imageFor(photo) { return photo.thumb || (photo.id.startsWith('demo-') ? 'https://images.unsplash.com/photo-1500534623283-312aade485b7?w=640&q=80' : `/api/photo/${photo.id}/thumbnail`); }
function fullImageFor(photo) { return photo.full || (photo.id.startsWith('demo-') ? imageFor(photo) : `/api/photo/${photo.id}`); }
function detailRows(photo) { const rows = [['Camera', photo.camera], ['Lens', photo.lens], ['Focal length', photo.focal_length ? `${Number(photo.focal_length).toFixed(1)} mm` : ''], ['Altitude', photo.altitude ? `${Number(photo.altitude).toFixed(0)} m` : ''], ['Direction', photo.direction !== null && photo.direction !== undefined ? `${Number(photo.direction).toFixed(0)}°` : '']]; return rows.filter(row => row[1]).map(row => `<div><span>${row[0]}</span><strong>${row[1]}</strong></div>`).join(''); }
function showToast(message) { const toast = $('toast'); toast.textContent = message; toast.classList.add('show'); setTimeout(() => toast.classList.remove('show'), 3500); }

function renderFilters() {
  const select = $('country-filter');
  select.innerHTML = '<option value="all">All countries</option>' + countries(state.photos).map(country => `<option value="${country}">${country}</option>`).join('');
}
function applyFilters() {
  const country = $('country-filter').value;
  const from = $('date-from').value;
  const to = $('date-to').value;
  state.filtered = state.photos.filter(photo => {
    const date = photo.date ? photo.date.slice(0, 10) : '';
    return (country === 'all' || photo.country === country) && (!from || date >= from) && (!to || date <= to);
  });
  render();
}
function markerIcon() { return L.divIcon({ className: 'photo-marker', html: '<span style="display:block;width:13px;height:13px;background:#e56845;border:3px solid #fbfaf6;border-radius:50%;box-shadow:0 1px 5px #15232188"></span>', iconSize: [13, 13], iconAnchor: [6, 6] }); }
function renderMap() {
  state.markers.forEach(marker => marker.remove()); state.markers = [];
  state.filtered.forEach(photo => {
    const marker = L.marker([photo.latitude, photo.longitude], { icon: markerIcon() }).addTo(state.map);
    marker.bindPopup(`<button class="popup-photo-button" data-photo-id="${photo.id}" type="button" aria-label="Open photo"><img class="popup-image" src="${imageFor(photo)}" alt=""></button><div class="popup-location"><strong>${[photo.city, photo.region, photo.country].filter(Boolean).join(', ')}</strong><span>${formatDate(photo.date)}</span></div>`);
    marker.on('click', () => selectPhoto(photo.id)); state.markers.push(marker);
  });
  if (state.filtered.length) state.map.fitBounds(L.latLngBounds(state.filtered.map(photo => [photo.latitude, photo.longitude])), { padding: [60, 60], maxZoom: 5 });
  updateVisible();
}
function updateVisible() {
  if (!state.map) return;
  const bounds = state.map.getBounds();
  state.visible = state.filtered.filter(photo => bounds.contains([photo.latitude, photo.longitude]));
  renderList();
  $('result-count').textContent = state.visible.length;
  $('result-title').textContent = state.visible.length === state.filtered.length ? 'Visible memories' : 'In this view';
}
function renderList() {
  const list = $('photo-list'); $('empty-state').hidden = state.visible.length > 0;
  list.innerHTML = state.visible.map(photo => `<article class="photo-card" data-id="${photo.id}"><img src="${imageFor(photo)}" alt="Photo from ${photo.country}" loading="lazy"><div><h3>${photo.country}</h3><p>${formatDate(photo.date)}</p></div></article>`).join('');
  list.querySelectorAll('.photo-card').forEach(card => card.addEventListener('click', () => openPhoto(card.dataset.id)));
}
function selectPhoto(id) { const photo = state.photos.find(item => item.id === id); if (!photo) return; state.markers.find(marker => marker.getLatLng().lat === photo.latitude && marker.getLatLng().lng === photo.longitude)?.openPopup(); }
function openPhoto(id) { const photo = state.photos.find(item => item.id === id); if (!photo) return; state.currentPhotoId = id; const index = state.visible.findIndex(item => item.id === id); $('modal-image').src = fullImageFor(photo); $('modal-image').alt = `Photo from ${photo.country}`; $('modal-title').textContent = photo.country; $('modal-place').textContent = [photo.city, photo.region].filter(Boolean).join(', '); $('modal-caption').textContent = formatDate(photo.date); $('modal-coordinates').textContent = `${photo.latitude.toFixed(5)}, ${photo.longitude.toFixed(5)}`; $('modal-details').innerHTML = detailRows(photo); $('previous-photo').disabled = index <= 0; $('next-photo').disabled = index < 0 || index >= state.visible.length - 1; $('photo-modal').hidden = false; }
function previousPhoto() { const index = state.visible.findIndex(photo => photo.id === state.currentPhotoId); if (index > 0) openPhoto(state.visible[index - 1].id); }
function nextPhoto() { const index = state.visible.findIndex(photo => photo.id === state.currentPhotoId); if (index >= 0 && index < state.visible.length - 1) openPhoto(state.visible[index + 1].id); }
function closePhoto() { $('photo-modal').hidden = true; $('modal-image').src = ''; }
function render() {
  $('photo-count').textContent = state.filtered.length; $('country-count').textContent = countries(state.filtered).length; $('map-caption').textContent = state.filtered.length ? 'Photos' : 'No locations selected'; renderMap();
}
async function init() {
  state.map = L.map('map', { zoomControl: false, worldCopyJump: true }).setView([-25, -64], 4);
  L.control.zoom({ position: 'topright' }).addTo(state.map);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors', maxZoom: 19 }).addTo(state.map);
  state.map.on('moveend', updateVisible);
  try { const response = await fetch('/api/photos'); state.photos = (await response.json()).photos; } catch (error) { try { const response = await fetch('/photos.json'); state.photos = (await response.json()).photos; } catch (exportError) { showToast('Could not load photo data.'); } }
  renderFilters(); applyFilters(); if (state.photos.some(photo => photo.id.startsWith('demo-'))) showToast('Demo data is active. Import a folder to see your own photos.');
}
$('country-filter').addEventListener('change', applyFilters); $('date-from').addEventListener('change', applyFilters); $('date-to').addEventListener('change', applyFilters); $('reset-filters').addEventListener('click', () => { $('country-filter').value = 'all'; $('date-from').value = ''; $('date-to').value = ''; applyFilters(); }); $('fit-map').addEventListener('click', () => { if (state.filtered.length) state.map.fitBounds(L.latLngBounds(state.filtered.map(photo => [photo.latitude, photo.longitude])), { padding: [60, 60], maxZoom: 5 }); }); $('close-modal').addEventListener('click', closePhoto); $('previous-photo').addEventListener('click', previousPhoto); $('next-photo').addEventListener('click', nextPhoto); document.querySelector('[data-close-modal]').addEventListener('click', closePhoto); document.addEventListener('keydown', event => { if (event.key === 'Escape') closePhoto(); if (event.key === 'ArrowLeft' && !$('photo-modal').hidden) previousPhoto(); if (event.key === 'ArrowRight' && !$('photo-modal').hidden) nextPhoto(); }); document.addEventListener('click', event => { const button = event.target.closest('.popup-photo-button'); if (button) openPhoto(button.dataset.photoId); });
init();
