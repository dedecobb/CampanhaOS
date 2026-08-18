import { useAuth } from "@/features/auth/context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { AgeBarChart } from "@/features/dashboard/components/AgeBarChart";
import { GenderPieChart } from "@/features/dashboard/components/GenderPieChart";
import { LeadershipBarChart } from "@/features/dashboard/components/LeadershipBarChart";
import { RegistrationGrowthChart } from "@/features/dashboard/components/RegistrationGrowthChart";
import { VoterGoalCard } from "@/features/dashboard/components/VoterGoalCard";
import { useDashboardStats } from "@/features/dashboard/hooks/use-dashboard-stats";

export function DashboardPage() {
  const { user } = useAuth();
  const { data, isLoading, isError } = useDashboardStats();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Olá, {user?.name}</h1>
        <p className="mt-1 text-muted-foreground">Panorama da campanha</p>
      </div>

      {isLoading && <p className="text-muted-foreground">Carregando estatísticas...</p>}
      {isError && <p className="text-destructive">Não foi possível carregar as estatísticas.</p>}

      {data && (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total de Eleitores</CardTitle>
              </CardHeader>
              <CardContent className="text-3xl font-semibold">{data.total_voters}</CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Autocadastro</CardTitle>
              </CardHeader>
              <CardContent className="text-3xl font-semibold">{data.self_registered_count}</CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Cadastrado pela Equipe</CardTitle>
              </CardHeader>
              <CardContent className="text-3xl font-semibold">{data.staff_registered_count}</CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Meta de Eleitores</CardTitle>
            </CardHeader>
            <CardContent>
              <VoterGoalCard totalVoters={data.total_voters} voterGoal={data.voter_goal} />
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Por Gênero</CardTitle>
              </CardHeader>
              <CardContent>
                <GenderPieChart genderBreakdown={data.gender_breakdown} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Por Faixa Etária</CardTitle>
              </CardHeader>
              <CardContent>
                <AgeBarChart ageBreakdown={data.age_breakdown} />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Cadastros nos Últimos 30 Dias</CardTitle>
            </CardHeader>
            <CardContent>
              <RegistrationGrowthChart registrationGrowth={data.registration_growth} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Eleitores por Liderança</CardTitle>
            </CardHeader>
            <CardContent>
              <LeadershipBarChart leadershipBreakdown={data.leadership_breakdown} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
