from rest_framework.response import Response
from rest_framework.views import APIView

from finance.models import Category
from finance.permissions import IsAdminOrReadOnly, IsAdminUser
from finance.response import created, ok
from finance.serializers.common_serializers import CategorySerializer


class CategoryListCreateView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        cat_type = request.query_params.get('type')
        nested = request.query_params.get('nested', '').lower() in ('1', 'true', 'yes')

        if nested:
            qs = Category.objects.filter(parent__isnull=True)
            if cat_type:
                qs = qs.filter(type=cat_type)
            return ok(CategorySerializer(qs, many=True).data)

        qs = Category.objects.all()
        if cat_type:
            qs = qs.filter(type=cat_type)
        return ok(CategorySerializer(qs, many=True).data)

    def post(self, request):
        ser = CategorySerializer(data=request.data)
        if not ser.is_valid():
            return Response({'code': 40001, 'message': str(ser.errors), 'data': None}, status=400)
        cat = ser.save(is_system=False)
        return created(CategorySerializer(cat).data)


class CategoryDetailView(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, pk):
        cat = Category.objects.get(pk=pk)
        return ok(CategorySerializer(cat).data)

    def patch(self, request, pk):
        cat = Category.objects.get(pk=pk)
        ser = CategorySerializer(cat, data=request.data, partial=True)
        if not ser.is_valid():
            return Response({'code': 40001, 'message': str(ser.errors), 'data': None}, status=400)
        ser.save()
        return ok(ser.data)

    def delete(self, request, pk):
        cat = Category.objects.get(pk=pk)
        if cat.is_system:
            return Response({'code': 40001, 'message': '系统预置分类不可删除', 'data': None}, status=400)
        cat.delete()
        return ok(None, '已删除')
