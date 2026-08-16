import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

interface LocationPickerProps {
  latitude: number | null;
  longitude: number | null;
  onChange: (latitude: number, longitude: number) => void;
}

// Centro aproximado do Brasil — usado só quando ainda não existe
// nenhuma coordenada (nem automática, nem manual) para centralizar o mapa.
const BRAZIL_CENTER: [number, number] = [-51.9253, -14.235];

/**
 * Pino ARRASTÁVEL para corrigir a posição manualmente quando a
 * geocodificação automática erra — o caso mais comum é rua interna de
 * condomínio (nome genérico tipo "Rua Três", sem mapeamento público
 * disponível para nenhum provedor de geocodificação acertar sozinho).
 *
 * Ao soltar o pino numa posição nova, `onChange` é chamado com a
 * coordenada exata — o formulário então envia essa coordenada como
 * MANUAL para a API, que (conforme já implementado nos casos de uso)
 * respeita coordenada manual e NÃO tenta geocodificar de novo por cima.
 */
export function LocationPicker({ latitude, longitude, onChange }: LocationPickerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markerRef = useRef<mapboxgl.Marker | null>(null);

  const hasToken = Boolean(import.meta.env.VITE_MAPBOX_ACCESS_TOKEN);
  const hasCoordinates = latitude !== null && longitude !== null;

  useEffect(() => {
    if (!hasToken || !containerRef.current || mapRef.current) return;

    mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;

    const initialCenter: [number, number] = hasCoordinates ? [longitude, latitude] : BRAZIL_CENTER;

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/streets-v12",
      center: initialCenter,
      zoom: hasCoordinates ? 16 : 3.5,
    });
    map.addControl(new mapboxgl.NavigationControl(), "top-right");

    const marker = new mapboxgl.Marker({ draggable: true }).setLngLat(initialCenter).addTo(map);
    marker.on("dragend", () => {
      const { lat, lng } = marker.getLngLat();
      onChange(lat, lng);
    });

    // Clicar em qualquer ponto do mapa também move o pino para lá —
    // mais fácil que precisar acertar o arrasto de primeira.
    map.on("click", (event) => {
      marker.setLngLat(event.lngLat);
      onChange(event.lngLat.lat, event.lngLat.lng);
    });

    mapRef.current = map;
    markerRef.current = marker;

    return () => {
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasToken]);

  if (!hasToken) {
    return (
      <p className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-400">
        Ajuste manual de posição indisponível — falta configurar o Mapbox no frontend.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">
        {hasCoordinates
          ? "Arraste o pino (ou clique no mapa) para corrigir a posição exata."
          : "Endereço ainda não foi geocodificado — clique no mapa para definir a posição manualmente."}
      </p>
      <div ref={containerRef} className="h-[300px] w-full rounded-lg border border-border" />
    </div>
  );
}
