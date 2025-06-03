# Deploying TerrainForge3D to Digital Ocean with Docker

This guide walks you through deploying the TerrainForge3D application to a Digital Ocean droplet using Docker and Docker Compose. It assumes you have a Digital Ocean account and a droplet ready (Ubuntu is recommended).

## Prerequisites

*   A Digital Ocean Droplet with SSH access.
*   Docker and Docker Compose installed on your droplet.
*   Git installed on your droplet.
*   An existing Cloudflare Tunnel setup that you can manage.
*   An existing Redis instance accessible from your Digital Ocean droplet.

## Deployment Steps

### 1. Install Docker and Docker Compose (if not already installed)

Connect to your Digital Ocean droplet via SSH.

**Install Docker:**
```bash
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker
```

**Install Docker Compose:**
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```
Verify installation: `docker-compose --version`

### 2. Clone the Repository

Clone the TerrainForge3D repository to your droplet:
```bash
git clone <your-repository-url> # Replace with your repository URL
cd <repository-directory-name> # e.g., cd terrainforge3d
```

### 3. Configure Environment Variables

Create a `.env` file in the root of the project directory:
```bash
cp .env.example .env
nano .env
```
Update the `.env` file with your specific configurations:

```env
# GitHub OAuth Configuration (Update these with your GitHub App credentials)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_CALLBACK_URL=http://your-domain.com/auth/github/callback # Or your Cloudflare Tunnel URL

# Session Configuration
SESSION_SECRET=generate_a_strong_random_secret_here # e.g., using: openssl rand -hex 32

# Redis Configuration (Update with your existing Redis details)
# Format: redis://[user:password@]host:port[/database_number]
# Example for a local Redis on default port, using database 0:
# REDIS_URL=redis://localhost:6379/0
# Example for a managed Redis with password:
# REDIS_URL=redis://:yourpassword@your-redis-host:your-redis-port/0
REDIS_URL=redis://your-redis-host:your-redis-port/0 # IMPORTANT: Update this

# Application Configuration
PORT=3123 # As per your requirement
NODE_ENV=production # Recommended for deployment
```
**Important:**
*   Replace placeholders like `your_github_client_id`, `your_github_client_secret`, `your-domain.com`, `generate_a_strong_random_secret_here`, and especially `REDIS_URL` with your actual values.
*   The `GITHUB_CALLBACK_URL` should be the final URL through which users will access your application (likely your Cloudflare Tunnel URL).

### 4. Set Volume Permissions

The application uses Docker volumes to store uploaded files, generated outputs, temporary job files, and the SQLite database. Run the provided script to create these directories (if they don't exist) and set appropriate permissions.

First, ensure the script is executable:
```bash
chmod +x set_permissions.sh
```
Then run the script:
```bash
./set_permissions.sh
```
This script will use `sudo` for `chown` and `chmod` operations. It defaults to setting ownership to UID/GID `1000:1000`. If your Docker container runs jobs as a different user, you might need to adjust the `TARGET_UID` and `TARGET_GID` in `set_permissions.sh`.

### 5. Build and Run the Application

Use Docker Compose to build the Docker image and run the application in detached mode:
```bash
docker-compose up -d --build
```
This command will:
*   `--build`: Build the Docker image based on the `Dockerfile`.
*   `-d`: Run the containers in detached mode (in the background).

### 6. Configure Cloudflare Tunnel

Since you already have Cloudflare Tunnels running:
1.  Access your Cloudflare dashboard.
2.  Go to your Tunnels configuration.
3.  You will likely need to add a new public hostname to an existing tunnel or create a new entry that points to the service running on your Digital Ocean droplet.
4.  The service URL will be `http://localhost:3123` (or `http://<your-droplet-ip>:3123` if your tunnel client is configured to access services by IP). Ensure the port matches the `PORT` you set in your `.env` file (e.g., 3123).
5.  Configure any additional Cloudflare settings for this hostname (e.g., Access policies, SSL/TLS settings).

Refer to the [Cloudflare Tunnels documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) for detailed instructions on managing your tunnels.

### 7. Application Access

Once the Docker containers are running and your Cloudflare Tunnel is configured, you should be able to access TerrainForge3D via the public URL you set up in Cloudflare.

## Basic Troubleshooting

*   **View Logs:** To see the logs from the running application container:
    ```bash
    docker-compose logs -f app
    ```
    (Replace `app` with your service name from `docker-compose.yml` if it's different, though it's `app` by default).
*   **Check Container Status:**
    ```bash
    docker-compose ps
    ```
*   **Permission Issues:** If the application reports permission errors related to file access, double-check the ownership and permissions set by `set_permissions.sh`. Ensure the UID/GID used matches the user running inside the Docker container. You can inspect the running container's user if needed:
    ```bash
    docker-compose exec app id
    ```
*   **Restart Application:**
    ```bash
    docker-compose restart app
    ```
*   **Stop Application:**
    ```bash
    docker-compose down
    ```

## Updating the Application

1.  Navigate to your project directory on the droplet.
2.  Pull the latest changes from your Git repository:
    ```bash
    git pull
    ```
3.  Rebuild the Docker image and restart the services:
    ```bash
    docker-compose up -d --build
    ```

This guide provides the core steps for deployment. Depending on your specific Digital Ocean and Cloudflare setup, minor adjustments might be necessary.
