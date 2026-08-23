# MADN Portable Node: Khumalo_Millers_Node

**Node ID**: `data-node-khumalo_millers_node-5eaa91`  
**Role**: `data_node`  
**Default Port**: `8011`  
**Created**: `2026-08-23T18:04:51.837910+00:00`  

## Quick Start
1. Ensure Python 3.9+ is installed.
2. Run the portable bootstrapper:
   ```bash
   python start.py
   ```
3. Open your browser to:
   [http://127.0.0.1:8011](http://127.0.0.1:8011)

## Remote Lifecycle Management
This node can be discovered, activated, deactivated, and managed remotely by any authorized Vault Node on the local subnet via REST API:
- `GET /api/node/status`
- `POST /api/node/activate`
- `POST /api/node/deactivate`
- `POST /api/storage/put`
- `GET /api/storage/get`
