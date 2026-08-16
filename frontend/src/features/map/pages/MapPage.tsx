import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { useVoterMapPoints } from "@/features/map/hooks/use-voter-map-points";

// Centro aproximado do Brasil, usado como fallback quando não há nenhum
// eleitor geocodificado ainda (mapa não pode abrir "no vazio").
const BRAZIL_CENTER: [number, number] = [-51.9253, -14.235];
const BRAZIL_DEFAULT_ZOOM = 3.5;

export function MapPage() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const [mapLoaded, setMapLoaded] = useState(false);

  const { data: points, isLoading, isError } = useVoterMapPoints();

  const hasToken = Boolean(import.meta.env.VITE_MAPBOX_ACCESS_TOKEN);

  // Inicializa o mapa UMA VEZ, na montagem do componente — não a cada
  // re-render (recriar o mapa toda hora seria caro e piscaria a tela).
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

  // Atualiza os marcadores sempre que os dados (ou o mapa) mudarem —
  // remove os antigos antes de adicionar os novos, para não acumular
  // marcador duplicado a cada atualização do React Query.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded || !points) return;

    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    if (points.length === 0) return;

    const bounds = new mapboxgl.LngLatBounds();

    for (const point of points) {
      const popup = new mapboxgl.Popup({ offset: 24 }).setHTML(
        `<strong>${escapeHtml(point.name)}</strong>${point.address ? `<br/>${escapeHtml(point.address)}` : ""}`,
      );
      const marker = new mapboxgl.Marker()
        .setLngLat([point.longitude, point.latitude])
        .setPopup(popup)
        .addTo(map);
      markersRef.current.push(marker);
      bounds.extend([point.longitude, point.latitude]);
    }

    map.fitBounds(bounds, { padding: 60, maxZoom: 14, duration: 500 });
  }, [points, mapLoaded]);

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
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Mapa de Eleitores</h1>
        {points && <p className="text-sm text-muted-foreground">{points.length} eleitor(es) geocodificado(s)</p>}
      </div>

      {isLoading && <p className="text-muted-foreground">Carregando...</p>}
      {isError && <p className="text-destructive">Não foi possível carregar os pontos do mapa.</p>}
      {points && points.length === 0 && (
        <p className="text-muted-foreground">
          Nenhum eleitor com endereço geocodificado ainda. Cadastre um endereço válido ao criar/editar um
          eleitor — a coordenada é preenchida automaticamente.
        </p>
      )}

      <div ref={mapContainerRef} className="h-[600px] w-full rounded-lg border border-border" />
    </div>
  );
}

/** Escapa HTML básico antes de injetar no popup (via setHTML) — nome/endereço vêm de dado do usuário. */
function escapeHtml(value: string): string {
  const div = document.createElement("div");
  div.textContent = value;
  return div.innerHTML;
}
