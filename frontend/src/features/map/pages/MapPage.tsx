import { useEffect, useMemo, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { useVoterMapPoints } from "@/features/map/hooks/use-voter-map-points";
import type { VoterMapPoint } from "@/features/map/api/types";

const BRAZIL_CENTER: [number, number] = [-51.9253, -14.235];
const BRAZIL_DEFAULT_ZOOM = 3.5;

interface GroupedPoint {
  latitude: number;
  longitude: number;
  voters: VoterMapPoint[];
}

/**
 * Agrupa eleitores com coordenada IDÊNTICA — endereço igual gera a mesma
 * coordenada exata na geocodificação, então isso identifica corretamente
 * quem mora no mesmo lugar (ex: mesma família).
 *
 * Sem esse agrupamento, dois pinos na mesma coordenada ficam empilhados
 * exatamente um em cima do outro no mapa — só o de cima aparece
 * clicável, o de baixo fica escondido (não é perda de dado, os dois
 * continuam cadastrados, é só um problema visual de sobreposição).
 */
function groupPointsByCoordinate(points: VoterMapPoint[]): GroupedPoint[] {
  const groups = new Map<string, GroupedPoint>();
  for (const point of points) {
    const key = `${point.latitude},${point.longitude}`;
    const existing = groups.get(key);
    if (existing) {
      existing.voters.push(point);
    } else {
      groups.set(key, { latitude: point.latitude, longitude: point.longitude, voters: [point] });
    }
  }
  return Array.from(groups.values());
}

function buildPopupHtml(group: GroupedPoint): string {
  if (group.voters.length === 1) {
    const voter = group.voters[0];
    return `<strong>${escapeHtml(voter.name)}</strong>${voter.address ? `<br/>${escapeHtml(voter.address)}` : ""}`;
  }

  const namesList = group.voters.map((v) => `<li>${escapeHtml(v.name)}</li>`).join("");
  const address = group.voters[0].address;
  return (
    `<strong>${group.voters.length} eleitores neste endereço</strong>` +
    `<ul style="margin:4px 0 0;padding-left:16px;">${namesList}</ul>` +
    (address ? `<span style="font-size:12px;color:#666;">${escapeHtml(address)}</span>` : "")
  );
}

/** Pino redondo com número — visualmente diferente do pino padrão, indica "mais de uma pessoa aqui". */
function createGroupMarkerElement(count: number): HTMLDivElement {
  const el = document.createElement("div");
  el.style.cssText = [
    "width:28px",
    "height:28px",
    "border-radius:9999px",
    "background:#f97316",
    "color:white",
    "font-weight:600",
    "font-size:13px",
    "display:flex",
    "align-items:center",
    "justify-content:center",
    "border:2px solid white",
    "box-shadow:0 1px 4px rgba(0,0,0,0.4)",
    "cursor:pointer",
  ].join(";");
  el.textContent = String(count);
  return el;
}

export function MapPage() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const [mapLoaded, setMapLoaded] = useState(false);

  const { data: points, isLoading, isError } = useVoterMapPoints();
  const groups = useMemo(() => (points ? groupPointsByCoordinate(points) : []), [points]);
  const groupedAddressCount = groups.filter((g) => g.voters.length > 1).length;

  const hasToken = Boolean(import.meta.env.VITE_MAPBOX_ACCESS_TOKEN);

  useEffect(() => {
    if (!hasToken || !mapContainerRef.current || mapRef.current) return;

    mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: "mapbox://styles/mapbox/streets-v12",
      center: BRAZIL_CENTER,
      zoom: BRAZIL_DEFAULT_ZOOM,
    });

    map.addControl(new mapboxgl.NavigationControl(), "top-right");
    map.on("load", () => setMapLoaded(true));

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [hasToken]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    if (groups.length === 0) return;

    const bounds = new mapboxgl.LngLatBounds();

    for (const group of groups) {
      const popup = new mapboxgl.Popup({ offset: 24 }).setHTML(buildPopupHtml(group));

      const marker =
        group.voters.length > 1
          ? new mapboxgl.Marker({ element: createGroupMarkerElement(group.voters.length) })
          : new mapboxgl.Marker();

      marker.setLngLat([group.longitude, group.latitude]).setPopup(popup).addTo(map);
      markersRef.current.push(marker);
      bounds.extend([group.longitude, group.latitude]);
    }

    map.fitBounds(bounds, { padding: 60, maxZoom: 14, duration: 500 });
  }, [groups, mapLoaded]);

  if (!hasToken) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Mapa de Eleitores</h1>
        <p className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-400">
          O mapa não está configurado — falta a variável de ambiente{" "}
          <code className="font-mono">VITE_MAPBOX_ACCESS_TOKEN</code> no frontend.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-semibold">Mapa de Eleitores</h1>
        {points && (
          <p className="text-sm text-muted-foreground">
            {points.length} eleitor(es) em {groups.length} endereço(s)
            {groupedAddressCount > 0 && ` — ${groupedAddressCount} com mais de uma pessoa`}
          </p>
        )}
      </div>

      {isLoading && <p className="text-muted-foreground">Carregando...</p>}
      {isError && <p className="text-destructive">Não foi possível carregar os pontos do mapa.</p>}
      {points && points.length === 0 && (
        <p className="text-muted-foreground">
          Nenhum eleitor com endereço geocodificado ainda. Cadastre um endereço válido ao criar/editar um
          eleitor — a coordenada é preenchida automaticamente.
        </p>
      )}
      {points && points.length > 0 && groupedAddressCount > 0 && (
        <p className="text-xs text-muted-foreground">
          🟠 Pino laranja com número = mais de um eleitor cadastrado no mesmo endereço (ex: mesma família).
          Clique para ver os nomes.
        </p>
      )}

      <div ref={mapContainerRef} className="h-[600px] w-full rounded-lg border border-border" />
    </div>
  );
}

function escapeHtml(value: string): string {
  const div = document.createElement("div");
  div.textContent = value;
  return div.innerHTML;
}
