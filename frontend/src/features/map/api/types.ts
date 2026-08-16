/**
 * Espelha VoterMapPointResponse (src/presentation/api/v1/schemas/voters.py).
 */
export interface VoterMapPoint {
  id: string;
  name: string;
  address: string | null;
  latitude: number;
  longitude: number;
}
