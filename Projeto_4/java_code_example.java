import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;

public class AppVulneravel {

    // VIOLAÇÃO: Credencial hardcoded (Regra 2.1)
    private static final String DB_URL = "jdbc:mysql://localhost/db";
    private static final String USER = "admin";
    private static final String PASS = "SenhaSuperSecreta123"; 

    public void verificarUsuario(String nome) {
        // VIOLAÇÃO: Variável não descritiva (Regra 5.2)
        String x = "SELECT * FROM users WHERE name = '" + nome + "'"; // VIOLAÇÃO: Concatenação SQL (Regra 4.1)

        try {
            Connection conn = DriverManager.getConnection(DB_URL, USER, PASS);
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery(x);

            while (rs.next()) {
                // VIOLAÇÃO: Uso de System.out.println (Regra 3.1)
                System.out.println("Usuario encontrado: " + rs.getString("id"));
            }
        } catch (Exception e) { 
            // VIOLAÇÃO: Catch genérico e printStackTrace (Regra 3.3 e 3.1)
            e.printStackTrace();
        }
    }

    // EM CONFORMIDADE: Método usando CamelCase e nome descritivo (Regra 5.2)
    public void calcularSalarioLiquido(double salarioBruto) {
        double imposto = salarioBruto * 0.15;
        // ... lógica de cálculo
    }
}