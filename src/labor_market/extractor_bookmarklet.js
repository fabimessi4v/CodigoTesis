/**
 * Bookmarklet / Script de Consola para LinkedIn Jobs
 * Proyecto de Tesis USACH - Análisis de Alineación Curricular
 * Autor: Fabián Ibarra Norambuena
 * 
 * USO COMO BOOKMARKLET:
 * 1. Crea un nuevo marcador en tu navegador (Chrome / Firefox / Edge).
 * 2. En la URL del marcador, pega el código que comienza con: javascript:(function(){ ... })();
 * 3. Entra a LinkedIn Jobs y navega a una oferta en Chile.
 * 4. Haz clic en el marcador. Se abrirá una pequeña ventana modal para confirmar el sector
 *    (TI o No-TI) y guardará la oferta en el almacenamiento local de tu navegador.
 * 5. Podrás descargar todas las ofertas acumuladas en 1 clic como 'ofertas_linkedin.json'.
 * 
 * USO ALTERNATIVO (CONSOLA DEVTOOLS):
 * Abre la consola (F12) en una oferta de LinkedIn y pega este script.
 */

(function () {
  // 1. Selectores de LinkedIn (compatibles con vista de búsqueda y vista individual)
  function getElementText(selectors) {
    for (let sel of selectors) {
      let el = document.querySelector(sel);
      if (el && el.innerText.trim()) {
        return el.innerText.trim();
      }
    }
    return "";
  }

  const titulo = getElementText([
    ".job-details-jobs-unified-top-card__job-title h1",
    ".jobs-unified-top-card__job-title",
    "h1.t-24",
    ".top-card-layout__title"
  ]) || document.title.split("|")[0].trim();

  const empresa = getElementText([
    ".job-details-jobs-unified-top-card__company-name a",
    ".job-details-jobs-unified-top-card__company-name",
    ".jobs-unified-top-card__company-name",
    ".topcard__org-name-link",
    ".top-card-layout__first-subline a"
  ]) || "Empresa no detectada";

  const ubicacion = getElementText([
    ".job-details-jobs-unified-top-card__primary-description-container span.tvm__text",
    ".jobs-unified-top-card__bullet",
    ".top-card-layout__first-subline .topcard__flavor--bullet"
  ]) || "Chile";

  const descripcionEl = document.querySelector(".jobs-description__content") ||
                        document.querySelector("#job-details") ||
                        document.querySelector(".show-more-less-html__markup") ||
                        document.querySelector(".jobs-box__html-content");

  const descripcion = descripcionEl ? descripcionEl.innerText.trim() : "";

  if (!descripcion) {
    alert("⚠️ No se pudo encontrar la descripción del empleo. Asegúrate de tener la oferta abierta y desplegada.");
    return;
  }

  // Detectar modalidad básica
  let modalidad = "No especificado";
  const descLower = (descripcion + " " + ubicacion).toLowerCase();
  if (descLower.includes("híbrido") || descLower.includes("hibrido")) modalidad = "Híbrido";
  else if (descLower.includes("remoto") || descLower.includes("teletrabajo")) modalidad = "Remoto";
  else if (descLower.includes("presencial")) modalidad = "Presencial";

  // Preguntar sector (TI vs No-TI)
  let sector = prompt("Selecciona el sector para esta oferta (escribe 1 para TI o 2 para No-TI):\n1. TI (Empresas de tecnología, software, consultoras TI)\n2. No-TI (Banca, Minería, Retail, Telecomunicaciones, Gobierno)", "1");
  
  if (sector === null) return; // Cancelado
  sector = (sector.trim() === "2" || sector.toLowerCase().includes("no")) ? "No-TI" : "TI";

  let subsector = prompt("Ingresa el subsector / rubro de la empresa:\n(Ej: Software House, Fintech, Banca, Minería, Retail, Telecomunicaciones)", sector === "TI" ? "Software House" : "Banca");
  if (!subsector) subsector = sector === "TI" ? "Tecnología" : "Sector Productivo Tradicional";

  // Almacenamiento local en navegador
  const STORAGE_KEY = "tesis_linkedin_ofertas_usach";
  let dataset = [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) dataset = JSON.parse(raw);
  } catch (e) {
    dataset = [];
  }

  const idNum = dataset.filter(o => o.sector === sector).length + 1;
  const idStr = `JOB-${sector === "TI" ? "TI" : "NOTI"}-${String(idNum).padStart(3, '0')}`;

  const nuevaOferta = {
    id: idStr,
    titulo: titulo,
    empresa: empresa,
    sector: sector,
    subsector: subsector,
    rol_categoria: "Pendiente clasificación",
    ubicacion: ubicacion,
    modalidad: modalidad,
    nivel_experiencia: "No especificado",
    requisitos_tecnicos: [],
    descripcion_completa: descripcion,
    url: window.location.href.split("?")[0],
    fecha_recoleccion: new Date().toISOString().split("T")[0]
  };

  // Verificar si la URL ya existe
  const yaExiste = dataset.some(o => o.url === nuevaOferta.url);
  if (yaExiste) {
    if (!confirm("⚠️ Esta oferta (o URL) ya fue guardada anteriormente. ¿Deseas agregarla de todas formas?")) {
      return;
    }
  }

  dataset.push(nuevaOferta);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(dataset));

  const totalTI = dataset.filter(o => o.sector === "TI").length;
  const totalNoTI = dataset.filter(o => o.sector === "No-TI").length;

  const msg = `✅ Oferta guardada exitosamente!\n\n` +
              `• ID: ${nuevaOferta.id}\n` +
              `• Cargo: ${nuevaOferta.titulo}\n` +
              `• Empresa: ${nuevaOferta.empresa} (${nuevaOferta.sector} - ${nuevaOferta.subsector})\n\n` +
              `📊 Progreso actual:\n` +
              `- Sector TI: ${totalTI} / 100\n` +
              `- Sector No-TI: ${totalNoTI} / 100\n` +
              `- Total: ${dataset.length} / 200\n\n` +
              `¿Deseas descargar el archivo JSON con todas las ofertas recolectadas hasta ahora?`;

  if (confirm(msg)) {
    const blob = new Blob([JSON.stringify(dataset, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ofertas_linkedin_${dataset.length}_recopiladas.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
})();
