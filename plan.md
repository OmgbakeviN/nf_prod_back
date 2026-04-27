Voici un **plan d’implémentation sur 7 jours** pour coder la plateforme avec :

* **Backend : Django + Django REST Framework**
* **Documentation API : drf-spectacular + Swagger**
* **Frontend : React JS + shadcn/ui**
* **Base de données : PostgreSQL de préférence**
* **Auth : JWT**
* **Emails : SMTP Django**
* **Uploads : fichiers locaux au début, Cloudinary/S3 plus tard**

DRF est bien adapté ici parce qu’on va utiliser des **ViewSets**, des **Serializers**, des **Permissions**, et drf-spectacular va générer la documentation OpenAPI/Swagger à partir de nos endpoints. DRF recommande aussi drf-spectacular pour générer et présenter les schémas OpenAPI. ([Django Rest Framework][1])
Pour shadcn/ui avec React, on partira sur **Vite + React + TypeScript** parce que c’est le setup recommandé dans la documentation shadcn/ui. ([Shadcn][2])
Pour les emails, Django utilise les paramètres SMTP comme `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` ou `EMAIL_USE_SSL`. ([Django Project][3])

---

# Architecture globale

## Backend Django

Structure proposée :

```txt
backend/
  config/
    settings.py
    urls.py
  apps/
    accounts/
    castings/
    projects/
    notifications/
    files/
    schedules/
  media/
  requirements.txt
```

Apps principales :

```txt
accounts        -> utilisateurs, rôles, invitations
castings        -> formulaires de casting, candidatures
projects        -> projets, membres, rôles dans projets
files           -> scripts, images, documents, validation
schedules       -> dates de tournage, répétitions, lieux
notifications   -> notifications email + in-app
```

---

## Frontend React

Structure proposée :

```txt
frontend/
  src/
    api/
    components/
    pages/
    layouts/
    hooks/
    lib/
    routes/
```

Pages principales :

```txt
/auth/login
/auth/register
/dashboard
/castings
/castings/:id/apply
/applications
/projects
/projects/:id
/projects/:id/files
/projects/:id/team
/projects/:id/schedule
/settings
```

---

# Règle importante pour Swagger

Chaque endpoint devra avoir :

* un `summary`
* une `description`
* les `request` serializers
* les `responses`
* les `tags`
* les permissions visibles
* les actions custom documentées avec `@extend_schema`

drf-spectacular permet justement de personnaliser les endpoints avec `@extend_schema`, surtout lorsque l’introspection automatique ne suffit pas. ([DRF Spectacular][4])

Exemple standard qu’on utilisera partout :

```python
from drf_spectacular.utils import extend_schema

@extend_schema(
    summary="Create a new casting",
    description="Allows a producer/admin to create a public casting form for a project.",
    tags=["Castings"],
    request=CastingCreateSerializer,
    responses={201: CastingDetailSerializer},
)
def create(self, request, *args, **kwargs):
    return super().create(request, *args, **kwargs)
```

---

# Jour 1 — Setup complet du projet

## Objectif

Préparer la base backend + frontend + documentation Swagger.

## Backend

À faire :

```txt
- Créer projet Django
- Installer DRF
- Installer drf-spectacular
- Installer simplejwt
- Installer corsheaders
- Configurer PostgreSQL ou SQLite temporaire
- Configurer media files
- Configurer Swagger
```

Packages backend :

```bash
pip install django djangorestframework drf-spectacular djangorestframework-simplejwt django-cors-headers pillow python-decouple
```

Endpoints techniques à avoir dès le jour 1 :

```txt
GET /api/schema/
GET /api/docs/
GET /api/redoc/
```

Documentation Swagger :

```txt
Tag: System
Description: API documentation and schema endpoints.
```

## Frontend

À faire :

```txt
- Créer projet Vite React TypeScript
- Installer Tailwind
- Installer shadcn/ui
- Installer axios
- Installer react-router-dom
- Installer lucide-react
```

Commandes :

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npx shadcn@latest init
npm install axios react-router-dom lucide-react
```

Composants shadcn à installer :

```bash
npx shadcn@latest add button card input label textarea select dialog dropdown-menu table badge tabs form toast
```

Livrable jour 1 :

```txt
- Backend démarre
- Frontend démarre
- Swagger visible
- Layout React de base prêt
```

---

# Jour 2 — Authentification, utilisateurs et rôles

## Objectif

Créer le système de comptes, rôles et permissions.

## Modèles

```txt
User
- email
- full_name
- phone
- role
- avatar
- is_active
- created_at
```

Rôles globaux :

```txt
ADMIN / PRODUCER
DIRECTOR
SCRIPTWRITER
ACTOR
CREW
```

## Endpoints

```txt
POST /api/auth/login/
POST /api/auth/refresh/
POST /api/auth/logout/
GET  /api/auth/me/

GET    /api/users/
POST   /api/users/invite/
GET    /api/users/{id}/
PATCH  /api/users/{id}/
DELETE /api/users/{id}/
```

## Access control

```txt
Producer/Admin:
- peut voir tous les users
- peut inviter un utilisateur
- peut modifier les rôles

Utilisateur normal:
- peut voir son profil
- peut modifier certaines infos personnelles
```

## Emails

Notifications à ajouter :

```txt
- Invitation à rejoindre la plateforme
- Compte créé
- Réinitialisation de mot de passe, si on l’ajoute
```

## Swagger

Tags :

```txt
Authentication
Users
```

Chaque endpoint doit avoir une description claire, par exemple :

```txt
POST /api/users/invite/
Description:
Allows a producer/admin to invite a new user to the production platform. 
An email invitation is sent to the invited user.
```

## Frontend

Pages :

```txt
/login
/dashboard
/users
/users/invite
```

Composants :

```txt
LoginForm
UserTable
InviteUserDialog
RoleBadge
```

Livrable jour 2 :

```txt
- Login JWT fonctionne
- Dashboard protégé
- Admin peut inviter un utilisateur
- Swagger documente auth + users
```

---

# Jour 3 — Module Casting

## Objectif

Créer le formulaire public de casting et la gestion des candidatures.

## Modèles

```txt
Casting
- title
- description
- project nullable
- is_public
- deadline
- created_by
- created_at

Application
- casting
- full_name
- age
- gender
- phone
- email
- location
- acting_experience
- experience_details
- portfolio_link
- languages
- special_skills
- camera_confidence
- available_for_filming
- available_for_rehearsals
- motivation
- reliability_reason
- preferred_role
- role_limitations
- headshot
- video
- commitment_confirmed
- signed_name
- status
- created_at
```

Statuts candidature :

```txt
PENDING
ACCEPTED
REJECTED
NEEDS_MORE_INFO
```

## Endpoints

```txt
GET    /api/castings/
POST   /api/castings/
GET    /api/castings/{id}/
PATCH  /api/castings/{id}/
DELETE /api/castings/{id}/

GET    /api/public/castings/{id}/
POST   /api/public/castings/{id}/apply/

GET    /api/applications/
GET    /api/applications/{id}/
POST   /api/applications/{id}/accept/
POST   /api/applications/{id}/reject/
POST   /api/applications/{id}/request-info/
```

## Access control

```txt
Public:
- peut voir un casting public
- peut soumettre une candidature

Producer/Admin:
- peut créer/modifier/supprimer castings
- peut voir toutes les candidatures
- peut accepter/refuser

Actor/Candidat:
- pas besoin de compte pour postuler au MVP
```

## Emails

```txt
- Confirmation de soumission au candidat
- Nouvelle candidature au producteur
- Candidature acceptée
- Candidature refusée
- Demande d’informations supplémentaires
```

## Swagger

Tags :

```txt
Castings
Applications
Public Castings
```

Descriptions importantes :

```txt
POST /api/public/castings/{id}/apply/
Description:
Public endpoint used by actors to submit an application form with headshot and video.

POST /api/applications/{id}/accept/
Description:
Allows a producer/admin to accept an actor application. The candidate receives an email notification.
```

## Frontend

Pages :

```txt
/castings
/castings/new
/castings/:id
/castings/:id/apply
/applications
/applications/:id
```

Composants :

```txt
CastingForm
PublicApplicationForm
ApplicationTable
ApplicationStatusBadge
ApplicationDetailsCard
```

Livrable jour 3 :

```txt
- Formulaire public fonctionnel
- Upload photo/vidéo
- Producteur voit les candidatures
- Accept/refuse fonctionne
- Emails de base envoyés
```

---

# Jour 4 — Module Projets et assignation d’équipe

## Objectif

Créer les projets et permettre au producteur d’assigner des membres.

## Modèles

```txt
Project
- title
- slug
- type
- genre
- short_description
- synopsis
- status
- cover_image
- created_by
- created_at
- updated_at
```

Statuts projet :

```txt
DRAFT
CASTING
PRE_PRODUCTION
PRODUCTION
POST_PRODUCTION
COMPLETED
CANCELLED
```

```txt
ProjectMember
- project
- user
- role
- character_name nullable
- character_description nullable
- joined_at
```

Rôles dans projet :

```txt
PRODUCER
DIRECTOR
SCRIPTWRITER
ACTOR
CAMERAMAN
EDITOR
CREW
```

## Endpoints

```txt
GET    /api/projects/
POST   /api/projects/
GET    /api/projects/{id}/
PATCH  /api/projects/{id}/
DELETE /api/projects/{id}/

GET    /api/projects/{id}/members/
POST   /api/projects/{id}/members/
PATCH  /api/projects/{id}/members/{member_id}/
DELETE /api/projects/{id}/members/{member_id}/
```

## Access control

```txt
Producer/Admin:
- voit tous les projets
- crée/modifie/supprime
- assigne les membres

Membre assigné:
- voit seulement les projets où il est assigné

Scriptwriter:
- voit les projets où il est assigné
- pourra uploader des scripts au jour 5

Actor:
- voit uniquement ses projets
- consulte les infos validées
```

## Emails

```txt
- Utilisateur ajouté à un projet
- Utilisateur retiré d’un projet
- Rôle modifié dans un projet
- Projet modifié
```

## Swagger

Tags :

```txt
Projects
Project Members
```

Descriptions importantes :

```txt
GET /api/projects/
Description:
Returns all projects for producers/admins. For normal users, returns only projects where the user is assigned.

POST /api/projects/{id}/members/
Description:
Allows a producer/admin to add a user to a project with a specific production role.
```

## Frontend

Pages :

```txt
/projects
/projects/new
/projects/:id
/projects/:id/team
```

Composants :

```txt
ProjectCard
ProjectForm
ProjectDetailsHeader
ProjectMembersTable
AddProjectMemberDialog
```

Livrable jour 4 :

```txt
- Producteur crée un projet
- Producteur assigne acteurs/scriptwriters
- Chaque user voit seulement ses projets
- Emails d’assignation fonctionnent
```

---

# Jour 5 — Scripts, fichiers, images et validation producteur

## Objectif

Créer le système de fichiers avec workflow de validation.

## Modèles

```txt
ProjectFile
- project
- uploaded_by
- title
- file
- file_type
- description
- version
- status
- reviewed_by
- reviewed_at
- rejection_reason
- created_at
```

Types :

```txt
SCRIPT
IMAGE
CONTRACT
STORYBOARD
PRODUCTION_NOTE
OTHER
```

Statuts :

```txt
DRAFT
PENDING_REVIEW
APPROVED
REJECTED
```

## Endpoints

```txt
GET    /api/projects/{id}/files/
POST   /api/projects/{id}/files/
GET    /api/projects/{id}/files/{file_id}/
PATCH  /api/projects/{id}/files/{file_id}/
DELETE /api/projects/{id}/files/{file_id}/

POST   /api/projects/{id}/files/{file_id}/submit-review/
POST   /api/projects/{id}/files/{file_id}/approve/
POST   /api/projects/{id}/files/{file_id}/reject/
```

## Access control

```txt
Producer/Admin:
- voit tous les fichiers
- approuve/rejette
- supprime

Scriptwriter:
- upload scripts
- modifie ses drafts
- soumet pour validation

Actor:
- voit seulement les fichiers APPROVED

Director:
- peut voir fichiers du projet
- peut proposer fichiers/notes selon permission
```

## Emails

```txt
- Nouveau script uploadé
- Script soumis pour validation
- Script approuvé
- Script rejeté
- Nouveau fichier approuvé disponible
```

## Swagger

Tags :

```txt
Project Files
Script Review
```

Descriptions importantes :

```txt
POST /api/projects/{id}/files/
Description:
Allows authorized project members to upload scripts, images, contracts or production documents.

POST /api/projects/{id}/files/{file_id}/approve/
Description:
Allows a producer/admin to approve a pending file. Approved files become visible to project members according to their role.
```

## Frontend

Pages :

```txt
/projects/:id/files
/projects/:id/scripts
```

Composants :

```txt
FileUploadCard
FileTable
FileStatusBadge
ScriptVersionCard
ApproveRejectDialog
```

Livrable jour 5 :

```txt
- Scriptwriter upload un script
- Producteur valide/rejette
- Acteurs voient uniquement les scripts validés
- Notifications email fonctionnent
```

---

# Jour 6 — Planning, lieux de tournage et notifications

## Objectif

Ajouter la planification de production.

## Modèles

```txt
ShootingLocation
- project
- name
- address
- city
- description
- image
- latitude nullable
- longitude nullable
```

```txt
ScheduleEvent
- project
- title
- event_type
- description
- location
- start_datetime
- end_datetime
- created_by
```

Types d’événements :

```txt
SHOOTING
REHEARSAL
MEETING
DEADLINE
OTHER
```

```txt
Notification
- user
- title
- message
- type
- is_read
- created_at
```

## Endpoints

```txt
GET    /api/projects/{id}/locations/
POST   /api/projects/{id}/locations/
PATCH  /api/projects/{id}/locations/{location_id}/
DELETE /api/projects/{id}/locations/{location_id}/

GET    /api/projects/{id}/schedule/
POST   /api/projects/{id}/schedule/
PATCH  /api/projects/{id}/schedule/{event_id}/
DELETE /api/projects/{id}/schedule/{event_id}/

GET    /api/notifications/
PATCH  /api/notifications/{id}/read/
POST   /api/notifications/read-all/
```

## Access control

```txt
Producer/Admin:
- gère lieux et planning

Director:
- peut proposer ou gérer planning selon décision produit

Membres projet:
- voient le planning des projets où ils sont assignés
```

## Emails

```txt
- Nouvelle date de tournage
- Date modifiée
- Date annulée
- Nouveau lieu ajouté
- Lieu modifié
- Rappel avant tournage, optionnel pour MVP
```

## Swagger

Tags :

```txt
Locations
Schedule
Notifications
```

Descriptions importantes :

```txt
POST /api/projects/{id}/schedule/
Description:
Creates a new production event such as shooting, rehearsal, meeting or deadline. Assigned project members receive notifications.

GET /api/notifications/
Description:
Returns the authenticated user’s in-app notifications.
```

## Frontend

Pages :

```txt
/projects/:id/schedule
/projects/:id/locations
/notifications
```

Composants :

```txt
ScheduleCalendar
ScheduleEventForm
LocationCard
NotificationDropdown
NotificationList
```

Livrable jour 6 :

```txt
- Planning par projet
- Lieux de tournage
- Notifications in-app
- Emails liés au planning
```

---

# Jour 7 — Nettoyage, sécurité, tests, UX finale

## Objectif

Stabiliser la plateforme pour une première version présentable.

## Backend

À faire :

```txt
- Revoir toutes les permissions
- Ajouter pagination
- Ajouter search/filter
- Ajouter validation fichiers
- Vérifier Swagger endpoint par endpoint
- Ajouter exemples Swagger
- Ajouter tests basiques
```

Endpoints à vérifier :

```txt
Auth
Users
Castings
Applications
Projects
Project Members
Files
Schedules
Locations
Notifications
```

## Swagger final

Chaque endpoint doit être vérifié dans :

```txt
/api/docs/
```

Checklist :

```txt
- Chaque endpoint a un tag
- Chaque endpoint a un summary
- Chaque endpoint a une description
- Les request bodies sont propres
- Les responses sont documentées
- Les endpoints publics sont visibles comme publics
- Les endpoints admin indiquent les permissions
```

## Frontend

À faire :

```txt
- Ajouter loading states
- Ajouter empty states
- Ajouter error states
- Ajouter toast notifications
- Ajouter dashboard stats
- Améliorer navigation sidebar
- Tester responsive mobile
```

Dashboard producteur :

```txt
- Nombre de projets
- Nombre de candidatures pending
- Nombre de scripts en attente
- Prochains tournages
```

Dashboard acteur/scriptwriter :

```txt
- Mes projets
- Mes prochaines dates
- Mes notifications
- Scripts disponibles
```

Livrable jour 7 :

```txt
- MVP propre
- Swagger complet
- Interface présentable
- Flow complet testable de bout en bout
```

---

# Flow complet à tester à la fin

## Flow 1 : Casting

```txt
1. Producteur crée un casting
2. Il partage le lien public
3. Candidat remplit le formulaire
4. Producteur reçoit email
5. Producteur accepte/refuse
6. Candidat reçoit email
```

## Flow 2 : Projet

```txt
1. Producteur crée un projet
2. Producteur ajoute un acteur
3. Acteur reçoit email
4. Acteur se connecte
5. Acteur voit uniquement ce projet
```

## Flow 3 : Script

```txt
1. Producteur ajoute un scriptwriter au projet
2. Scriptwriter upload un script
3. Producteur reçoit notification
4. Producteur approuve
5. Acteurs reçoivent email
6. Acteurs voient le script validé
```

## Flow 4 : Planning

```txt
1. Producteur ajoute une date de tournage
2. Les membres du projet reçoivent une notification
3. Chaque membre voit la date dans son dashboard
```

---

# Priorité MVP réelle

Pour ne pas se perdre, voici l’ordre strict :

```txt
1. Auth + rôles
2. Casting public
3. Accept / reject applications
4. Projets
5. Assignation équipe
6. Upload scripts
7. Validation scripts
8. Planning
9. Notifications
10. Finitions UI
```

---

# Stack recommandée

## Backend

```txt
Django
Django REST Framework
drf-spectacular
SimpleJWT
django-cors-headers
Pillow
python-decouple
PostgreSQL
```

## Frontend

```txt
React + Vite + TypeScript
shadcn/ui
Tailwind CSS
Axios
React Router DOM
Lucide React
React Hook Form
Zod
```

## Documentation

```txt
Swagger UI: /api/docs/
Schema OpenAPI: /api/schema/
ReDoc: /api/redoc/
```

---

# Règle de codage qu’on va suivre

À chaque module, on fera dans cet ordre :

```txt
1. models.py
2. serializers.py
3. permissions.py
4. views.py
5. urls.py
6. swagger avec @extend_schema
7. tests rapides avec Swagger
8. frontend page
9. intégration axios
10. UI shadcn
```

Comme ça, on ne code pas dans le désordre.

---

# Plan de démarrage immédiat

La première chose à coder sera :

```txt
Jour 1 :
- Setup Django
- Setup DRF
- Setup drf-spectacular
- Setup JWT
- Setup React + shadcn/ui
- Première page Login
- Première page Dashboard
```

Ensuite on attaquera directement :

```txt
Jour 2 :
- Custom User
- Rôles
- Permissions
- Invitation utilisateur
```

Le bon choix est de construire d’abord une base solide, parce que tout le reste dépend de :

```txt
User
Role
Permission
Project access
Swagger documentation
```

[1]: https://www.django-rest-framework.org/api-guide/viewsets/?utm_source=chatgpt.com "Viewsets"
[2]: https://ui.shadcn.com/docs/installation/vite?utm_source=chatgpt.com "Vite - Shadcn UI"
[3]: https://docs.djangoproject.com/en/6.0/topics/email/?utm_source=chatgpt.com "Sending email"
[4]: https://drf-spectacular.readthedocs.io/en/latest/customization.html?utm_source=chatgpt.com "Workflow & schema customization - DRF Spectacular"
