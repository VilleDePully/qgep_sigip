#!/bin/bash

OIDPREFIX="ch15z36d"

set -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/..

export PGSERVICE=pg_qgep_sige

psql -c 'DROP SCHEMA IF EXISTS qgep CASCADE'
psql -c 'DROP SCHEMA IF EXISTS sige_assainissement CASCADE'
psql -c 'DROP SCHEMA IF EXISTS sa CASCADE'
${DIR}/QGEP-Datamodel/scripts/db_setup.sh

psql -c "UPDATE qgep.is_oid_prefixes SET active=TRUE WHERE prefix='${OIDPREFIX}'"
psql -c "UPDATE qgep.is_oid_prefixes SET active=FALSE WHERE prefix<>'${OIDPREFIX}'"

pg_restore -d qgep_sige ${DIR}/migration/dump_topobase.backup
psql -c 'ALTER SCHEMA sige_assainissement RENAME TO sa'

psql -f ${DIR}/migration/mappings/function_hierarchic.sql
psql -f ${DIR}/migration/mappings/reach_horizontal_positioning.sql
psql -f ${DIR}/migration/mappings/manhole_function.sql
psql -f ${DIR}/migration/mappings/usage_current.sql

psql -f ${DIR}/migration/organisations.sql
psql -f ${DIR}/migration/cover_manhole.sql
psql -f ${DIR}/migration/profiles.sql
psql -f ${DIR}/migration/reach_channel.sql

OWNER=qgep SCHEMA=qgep DATABASE=qgep_sige ${DIR}/QGEP-Datamodel/scripts/change_owner.sh