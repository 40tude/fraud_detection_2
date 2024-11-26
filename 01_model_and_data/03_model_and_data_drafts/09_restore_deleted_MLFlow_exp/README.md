mlflow experiments restore --experiment-id 34



Chat GPT

Pour réactiver une expérience supprimée dans MLFlow, il est important de comprendre qu'une fois une expérience marquée comme "deleted", MLFlow la conserve dans un état supprimé, ce qui empêche de relancer des runs associés tant qu'elle n'est pas restaurée.

Voici quelques pistes pour résoudre le problème :

### 1. Réactiver l'Expérience Supprimée
Vous pouvez essayer de réactiver l'expérience supprimée en utilisant la commande `mlflow experiments restore`. Cette commande est utile pour récupérer une expérience supprimée, si elle est toujours disponible dans le registre des expériences MLFlow.

Par exemple, vous pouvez essayer de restaurer l'expérience avec l'ID `34` de cette manière :

```bash
mlflow experiments restore --experiment-id 34
```

Cette commande devrait permettre de réactiver l'expérience supprimée. Assurez-vous que vous êtes connecté au serveur MLFlow Tracking approprié avant d'exécuter cette commande.

### 2. Utiliser un Nouveau Nom d'Expérience
Étant donné que vous définissez le nom d'expérience dynamiquement avec la date du jour, une solution simple serait d'attendre le lendemain pour que la valeur de `$currentDate` change. Cela devrait créer une nouvelle expérience sans problème, car le nom sera différent de celui déjà supprimé.

Cependant, si vous voulez relancer le run dès maintenant, vous pourriez simplement changer le suffixe du nom d'expérience pour contourner le problème. Par exemple, vous pourriez ajouter un numéro d'essai supplémentaire ou un timestamp précis :

```powershell
$currentDate = Get-Date -Format "yyyyMMdd-HHmmss"
$env:MLFLOW_EXPERIMENT_NAME = "sklearn-$currentDate"
```

Cela générera un nouveau nom unique, même si vous relancez le même jour.

### 3. Suppression Définitive de l'Expérience
Il est aussi possible que l'expérience ait besoin d'être supprimée définitivement si vous ne voulez plus y avoir accès. Vous pouvez essayer de la supprimer définitivement avec la commande :

```bash
mlflow experiments delete --experiment-id 34
```

Puis, recréez l'expérience avec un nouveau run. Cela pourrait résoudre le conflit si MLFlow tente de recréer une expérience supprimée.

### 4. Accéder au Serveur PostgreSQL sur Heroku
Puisque votre MLFlow Tracking est hébergé sur une base PostgreSQL sur Heroku, vous pourriez également essayer de vérifier directement dans la base de données. Connectez-vous à votre base de données sur Heroku avec PgAdmin, et localisez la table des expériences (habituellement `experiments`). Vérifiez si l'expérience 34 est listée avec un état "deleted", et si oui, vous pouvez essayer de changer son état à "active".

```sql
UPDATE experiments
SET lifecycle_stage = 'active'
WHERE experiment_id = 34;
```

**Note :** Manipuler directement la base de données peut être risqué et doit être fait avec précaution. Assurez-vous de bien comprendre l'impact des modifications directes.

### Conclusion
- Pour réactiver l'expérience supprimée, la commande `mlflow experiments restore` est souvent la solution la plus directe.
- Si vous souhaitez éviter la gestion manuelle, modifier le nom de l'expérience pour obtenir un nom unique est une solution rapide.
- Modifier la base PostgreSQL manuellement est possible, mais nécessite de la prudence.

Essayer l'une de ces solutions devrait vous permettre de résoudre le problème. Si vous avez encore des questions ou si vous avez besoin d'autres précisions, n'hésitez pas à demander !