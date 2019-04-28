

def read_n_clean(path, error_log, duplicate_log, f):
    """
    read an obj and clean it, otherwise return None
    :param path: input path of obj
    :param error_log: path to error log. str ends with ".txt"
    :param duplicate_log: path to log file containing all mesh with duplicated points
    :param f: file name to be written to the error_log and dupilcate_log
    :return: None if mesh too wrong. Otherwise vertice_list and f_list
    """
    rewrite = False  # a flag to note this file needs to be rewritten

    header, mu_line, semantics, v_list, f_list = parse_obj(path)

    # check if vertice list and face list have duplicates
    unique_v, _ = unique_items(v_list)
    unique_f, unique_f_id = unique_items(f_list)

    if len(v_list) != len(unique_v) or len(f_list) != len(unique_f):
        rewrite = True
        if len(v_list) != len(unique_v):
            print("Has duplicated vertices! Will clean and rewrite.")
        else:
            print("Has duplicated faces! Will clean and rewrite")
        with open(duplicate_log, "w+") as d:
            d.write(f)

    # check if any of the (unique) faces has duplicated vertices
    for i, face_with_id in enumerate(unique_f):
        # f is a list of integers so we do it faster!
        if len(face_with_id) != len(set(face_with_id)):
            rewrite = True
            print("Has duplicated vertices in at least one faces! Will clean and rewrite.")
            with open(duplicate_log, "w+") as d:
                d.write(f)
            unique_local_f, _ = unique_items(face_with_id)
            unique_f[i] = unique_local_f    # substitute the original wrong face with this new face

    # then check if faces all valid
    print(unique_v)
    print(unique_f)
    face_with_points_3d = concrete_faces(unique_v, unique_f)
    if not validate_faces(face_with_points_3d):
        # not all faces are planar
        log_error(error_log, f)
        return None

    # test if rewrite is correct, modify later
    if not rewrite:
        ob = f.split(".")[0]
        header = "# " + ob + "\n# rewrite created on " + datetime.datetime.today().strftime('%Y-%m-%d') + "\n"
        mu = mu_line[7:].strip().split(" ")
        unique_semantics = [semantics[i] for i in unique_f_id]
        write_poly_obj(path, header, mu, unique_semantics, unique_v, unique_f)

    return unique_v, unique_f, face_with_points_3d


def unique_items(L):
    found = []
    found_id = []
    for i, item in enumerate(L):
        if item not in found:
            found.append(item)
            found_id.append(i)
    return found, found_id



# def project2t3():
#     """
#     project 2D points back to 2D points
#     :param tris: output of the triangle.triangulate() function. list of triangles. list of list of 2D points
#     :return:
#     """   # -- Store the vertices of each triangle in a list
#     tri_points = []  # store all the traingles. a list of list of list
#     for tri in tris:
#         # print("now print tri")
#         # print(tri)
#         tri_points_tmp = []   # a single triangle. list of lists
#         for v in tri.tolist():
#             try:
#                 vert_adj = [0] * 3   # initialize a vertex!
#                 if YZ:
#                     vert_adj[0] = temppolypoints[0][0]
#                     vert_adj[1] = vert[v][0]
#                     vert_adj[2] = vert[v][1]
#                 elif vertical:
#                     vert_adj[0] = vert[v][0]
#                     vert_adj[2] = vert[v][1]
#                     vert_adj[1] = polygon3dmodule.get_y(pl, vert_adj[0], vert_adj[2])
#                 else:
#                     vert_adj[0] = vert[v][0]
#                     vert_adj[1] = vert[v][1]
#                     vert_adj[2] = polygon3dmodule.get_height(pl, vert_adj[0], vert_adj[1])
#             except Exception as e:
#                 print(e)
#                 return None
#             try:
#                 # print("now print vert adj")
#                 # print(vert_adj)
#                 match_vert = find_match(vertices, vert_adj)
#             except Exception:
#                 print("Calculated point not found!!")
#                 return None
#             tri_points_tmp.append(match_vert)
#         try:
#             tri_normal = polygon3dmodule.unit_normal(tri_points_tmp[0], tri_points_tmp[1], tri_points_tmp[2])
#         except:
#             print("Triangle normal incorrect!!\n")
#             return None
#         if polygon3dmodule.compare_normals(normal, tri_normal):
#             tri_points.append(tri_points_tmp)
#         else:
#             tri_points_tmp = polygon3dmodule.reverse_vertices(tri_points_tmp)
#             tri_points.append(tri_points_tmp)

