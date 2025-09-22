from repository.models import SFCStatus, Status


def status_service(user, name, message, step=None, error=False):
    try:
        sfc = SFCStatus.objects.get(client=user, name=name)
        Status.objects.create(sfcstatus=sfc, message=message, error=error)
    except SFCStatus.DoesNotExist:
        sfc = SFCStatus.objects.create(client=user, name=name)
        Status.objects.create(sfcstatus=sfc, message=message, error=error)

    if step:
        sfc.step = step
        sfc.save()
    return sfc
