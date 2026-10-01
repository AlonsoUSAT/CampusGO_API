from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from services.viaje_service import ViajeService
from utils.response import success_response, error_response

viaje_bp = Blueprint("viajes", __name__)


@viaje_bp.route("/api/viajes", methods=["POST"])
@jwt_required()
def crear_viaje():
    claims = get_jwt()
    if claims.get("rol") != "CONDUCTOR":
        return error_response("Se requiere rol CONDUCTOR", 403)

    datos = request.get_json(silent=True) or {}
    service = ViajeService()
    data, message, code = service.crear(
        get_jwt_identity(),
        datos
    )
    if data is None:
        return error_response(message, code)
    return success_response(data, message, code)


@viaje_bp.route("/api/viajes", methods=["GET"])
@jwt_required()
def listar_viajes():
    filtros = {
        "origen": request.args.get("origen"),
        "destino": request.args.get("destino"),
        "fecha": request.args.get("fecha"),
        "estado": request.args.get("estado"),
        # Ejercicio 1: Rango de precio
        "precio_min": request.args.get("precio_min"),
        "precio_max": request.args.get("precio_max"),
        # Ejercicio 2: Solo viajes con cupos disponibles
        "solo_disponibles": request.args.get("solo_disponibles"),
        # Ejercicio 3: Rango de fechas
        "desde": request.args.get("desde"),
        "hasta": request.args.get("hasta")
    }
    data, message, code = ViajeService().listar(filtros)
    if data is None:
        return error_response(message, code)
    return success_response(data, message, code)


@viaje_bp.route("/api/viajes/resumen", methods=["GET"])
@jwt_required()
def resumen_viajes():
    """Ejercicio 10: Reporte de viajes agrupados por estado para el conductor autenticado."""
    claims = get_jwt()
    if claims.get("rol") != "CONDUCTOR":
        return error_response("Se requiere rol CONDUCTOR", 403)

    data, message, code = ViajeService().resumen_por_estado(get_jwt_identity())
    if data is None:
        return error_response(message, code)
    return success_response(data, message, code)


@viaje_bp.route("/api/viajes/mios", methods=["GET"])
@jwt_required()
def listar_mis_viajes():
    """Ejercicio 4: Consultar mis viajes publicados con filtro opcional ?estado=..."""
    claims = get_jwt()
    if claims.get("rol") != "CONDUCTOR":
        return error_response("Se requiere rol CONDUCTOR", 403)

    estado_filtro = request.args.get("estado")
    data, message, code = ViajeService().listar_mios(
        get_jwt_identity(),
        estado=estado_filtro
    )
    if data is None:
        return error_response(message, code)
    return success_response(data, message, code)


@viaje_bp.route("/api/viajes/<int:viaje_id>", methods=["GET"])
@jwt_required()
def obtener_viaje(viaje_id):
    """Ejercicio 8: Detalle enriquecido de un viaje con datos del conductor."""
    data, message, code = ViajeService().obtener(viaje_id)
    if data is None:
        return error_response(message, code)
    return success_response(data, message, code)


@viaje_bp.route("/api/viajes/<int:viaje_id>", methods=["PUT"])
@jwt_required()
def actualizar_viaje(viaje_id):
    claims = get_jwt()
    if claims.get("rol") != "CONDUCTOR":
        return error_response("Se requiere rol CONDUCTOR", 403)

    datos = request.get_json(silent=True) or {}
    data, message, code = ViajeService().actualizar(
        get_jwt_identity(),
        viaje_id,
        datos
    )
    if data is None:
        return error_response(message, code)
    return success_response(data, message, code)


@viaje_bp.route("/api/viajes/<int:viaje_id>/cupos", methods=["PATCH"])
@jwt_required()
def actualizar_cupos(viaje_id):
    """Ejercicio 5: Actualizar solamente los cupos de un viaje."""
    claims = get_jwt()
    if claims.get("rol") != "CONDUCTOR":
        return error_response("Se requiere rol CONDUCTOR", 403)

    datos = request.get_json(silent=True) or {}
    data, message, code = ViajeService().actualizar_cupos(
        get_jwt_identity(),
        viaje_id,
        datos
    )
    if data is None:
        return error_response(message, code)
    return success_response(data, message, code)


@viaje_bp.route("/api/viajes/<int:viaje_id>/estado", methods=["PATCH"])
@jwt_required()
def cambiar_estado(viaje_id):
    """Ejercicio 6: Cambiar el estado del viaje."""
    claims = get_jwt()
    if claims.get("rol") != "CONDUCTOR":
        return error_response("Se requiere rol CONDUCTOR", 403)

    datos = request.get_json(silent=True) or {}
    data, message, code = ViajeService().cambiar_estado(
        get_jwt_identity(),
        viaje_id,
        datos
    )
    if data is None:
        return error_response(message, code)
    return success_response(data, message, code)


@viaje_bp.route("/api/viajes/<int:viaje_id>", methods=["DELETE"])
@jwt_required()
def cancelar_viaje(viaje_id):
    """Ejercicio 9: Cancelar un viaje con restricciones y trazabilidad."""
    claims = get_jwt()
    if claims.get("rol") != "CONDUCTOR":
        return error_response("Se requiere rol CONDUCTOR", 403)

    data, message, code = ViajeService().cancelar(
        get_jwt_identity(),
        viaje_id
    )
    if data is None:
        return error_response(message, code)
    return success_response(data, message, code)
