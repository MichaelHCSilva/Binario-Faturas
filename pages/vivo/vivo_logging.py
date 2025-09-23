import logging

logger = logging.getLogger(__name__)

log_stats = {
    "total": 0,
    "sucesso": 0,
    "falha": 0,
    "falhas": []
}

def log_fatura(page, pos, total_page, pdf_name, sucesso=True, motivo=None):
    log_stats["total"] += 1
    if sucesso:
        log_stats["sucesso"] += 1
        logger.info(f"Fatura {pos}/{total_page} baixada e processada com sucesso: {pdf_name}")
    else:
        log_stats["falha"] += 1
        logger.error(f"Fatura {pos}/{total_page} falha ao processar: {pdf_name} — {motivo}")
        log_stats["falhas"].append(
            f"- Página {page}, posição {pos}: {pdf_name} ({motivo})"
        )
