from huey.contrib.djhuey import task

from lemarche.utils.apis.geocoding import get_geocoding_data


@task()
def set_siae_coords(model, siae):
    """
    Why do we use filter+update here? To avoid calling Siae.post_save signal again (recursion)
    """
    geocoding_data = get_geocoding_data(siae.address + " " + siae.city, post_code=siae.post_code)
    if geocoding_data:
        if siae.post_code != geocoding_data["post_code"]:
            if not siae.post_code or (siae.post_code[:2] == geocoding_data["post_code"][:2]):
                # update post_code as well
                model.objects.filter(id=siae.id).update(
                    coords=geocoding_data["coords"], post_code=geocoding_data["post_code"]
                )
            else:
                print(
                    f"Geocoding found a different place,{siae.name},{siae.post_code},{geocoding_data['post_code']}"  # noqa
                )
        else:
            # s.coords = geocoding_data["coords"]
            model.objects.filter(id=siae.id).update(coords=geocoding_data["coords"])
    else:
        print(f"Geocoding not found,{siae.name},{siae.post_code}")
